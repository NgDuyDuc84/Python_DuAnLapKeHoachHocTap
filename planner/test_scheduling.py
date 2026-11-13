from datetime import date, time, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse

from studies.models import Material, Task

from .forms import PlanWeekForm
from .models import BusyEvent, StudyPlan, StudyPreference, StudySession
from .services.availability import at_time, build_week
from .services.scheduling import PlanError, apply_plan, calculate_schedule, create_draft

MONDAY = date(2026, 11, 16)


def moment(day, hour=0, minute=0):
    return at_time(date(2026, 11, day), time(hour, minute))


class SchedulingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="schedule_owner")
        cls.other = get_user_model().objects.create_user(username="schedule_other")
        cls.preferences = StudyPreference.objects.create(
            owner=cls.owner, study_days=[0], study_start=time(8), study_end=time(12),
            max_daily_minutes=180, session_minutes=50, break_minutes=10,
        )

    def setUp(self):
        self.clock = patch("planner.services.scheduling.timezone.now", return_value=moment(15))
        self.clock.start()
        self.addCleanup(self.clock.stop)

    def task(self, **kwargs):
        values = {"owner": self.owner, "title": "Học Python", "deadline": moment(16, 12),
                  "estimated_minutes": 120, "remaining_minutes": 120}
        values.update(kwargs)
        return Task.objects.create(**values)

    def preference(self, **kwargs):
        StudyPreference.objects.filter(owner=self.owner).update(**kwargs)
        self.preferences.refresh_from_db()

    def result(self, **kwargs):
        return calculate_schedule(self.owner, MONDAY, **kwargs)

    def existing(self, task, start, end, week=MONDAY):
        plan = StudyPlan.objects.create(owner=self.owner, week_start=week, applied_at=moment(15))
        return StudySession.objects.create(owner=self.owner, plan=plan, task=task, starts_at=start, ends_at=end)

    def test_split_task_has_preferred_sessions_break_and_short_last_session(self):
        task = self.task()
        result = self.result()
        self.assertEqual(result["sessions"], [
            (task.pk, moment(16, 8), moment(16, 8, 50)),
            (task.pk, moment(16, 9), moment(16, 9, 50)),
            (task.pk, moment(16, 10), moment(16, 10, 20)),
        ])
        self.assertEqual(result["report"][0]["unallocated_minutes"], 0)

    def test_deadline_then_priority_order_and_daily_budget(self):
        self.preference(max_daily_minutes=60)
        late = self.task(title="Hạn sau", deadline=moment(17, 12), priority=3)
        low = self.task(title="Ưu tiên thấp", priority=1)
        high = self.task(title="Ưu tiên cao", priority=3)
        result = self.result()
        self.assertEqual({s[0] for s in result["sessions"]}, {high.pk})
        self.assertEqual([r["task_id"] for r in result["report"]], [high.pk, low.pk, late.pk])
        self.assertEqual(sum((b - a).total_seconds() // 60 for _, a, b in result["sessions"]), 60)

    def test_deadline_clips_session_to_exact_minute(self):
        self.task(deadline=moment(16, 8, 30))
        result = self.result()
        self.assertEqual(result["sessions"][0][1:], (moment(16, 8), moment(16, 8, 30)))
        self.assertEqual(result["report"][0]["unallocated_minutes"], 90)

    def test_recurring_and_overlapping_busy_events_are_respected(self):
        task = self.task(remaining_minutes=90)
        for start, end, repeats in ((moment(9, 8), moment(9, 9), True),
                                    (moment(16, 10), moment(16, 11), False),
                                    (moment(16, 10, 30), moment(16, 11), False)):
            BusyEvent.objects.create(owner=self.owner, title="Bận", starts_at=start, ends_at=end, repeat_weekly=repeats)
        self.assertEqual(self.result()["sessions"], [
            (task.pk, moment(16, 9), moment(16, 9, 50)),
            (task.pk, moment(16, 11), moment(16, 11, 40)),
        ])

    def test_overnight_recurrence_from_previous_week_blocks_monday(self):
        self.task()
        BusyEvent.objects.create(owner=self.owner, title="Ca đêm", starts_at=moment(8, 22),
                                 ends_at=moment(9, 9), repeat_weekly=True)
        self.assertEqual(self.result()["sessions"][0][1], moment(16, 9))

    def test_unsplittable_task_uses_single_contiguous_slot_longer_than_preference(self):
        task = self.task(can_split=False)
        self.assertEqual(self.result()["sessions"], [(task.pk, moment(16, 8), moment(16, 10))])

    def test_unsplittable_task_rejected_when_only_fragments_or_budget_remain(self):
        self.task(can_split=False)
        BusyEvent.objects.create(owner=self.owner, title="Bận", starts_at=moment(16, 9), ends_at=moment(16, 11))
        result = self.result()
        self.assertEqual(result["sessions"], [])
        self.assertIn("liên tục", result["report"][0]["reason"])
        BusyEvent.objects.all().delete()
        self.preference(max_daily_minutes=60)
        self.assertEqual(self.result()["sessions"], [])

    def test_current_time_rounds_up_and_does_not_schedule_in_the_past(self):
        self.task()
        result = self.result(now=moment(16, 8, 15) + timedelta(seconds=1))
        self.assertEqual(result["sessions"][0][1], moment(16, 8, 16))

    def test_unselected_days_completed_and_foreign_tasks_not_scheduled(self):
        self.task(status=Task.Status.DONE, remaining_minutes=0)
        self.task(owner=self.other)
        self.assertEqual(self.result()["report"], [])
        self.task()
        self.preference(study_days=[])
        result = self.result()
        self.assertEqual(result["sessions"], [])
        self.assertEqual(result["report"][0]["unallocated_minutes"], 120)

    def test_overdue_and_before_week_tasks_report_reasons(self):
        self.task(deadline=moment(14))
        self.task(deadline=moment(15, 12))
        result = self.result()
        self.assertEqual(result["sessions"], [])
        self.assertIn("quá hạn", result["report"][0]["reason"])
        self.assertIn("trước tuần", result["report"][1]["reason"])

    def test_future_deadline_reports_week_shortfall_without_claiming_overdue(self):
        self.task(deadline=moment(30), remaining_minutes=300)
        row = self.result()["report"][0]
        self.assertEqual((row["scheduled_minutes"], row["unallocated_minutes"]), (180, 120))
        self.assertIn("tuần sau", row["reason"])

    def test_existing_sessions_reduce_need_block_breaks_and_use_daily_budget(self):
        task = self.task()
        self.preference(max_daily_minutes=100)
        self.existing(task, moment(16, 8), moment(16, 8, 50))
        result = self.result()
        self.assertEqual(result["sessions"], [(task.pk, moment(16, 9), moment(16, 9, 50))])
        row = result["report"][0]
        self.assertEqual((row["existing_minutes"], row["scheduled_minutes"], row["unallocated_minutes"]), (50, 50, 20))

    def test_future_sessions_in_other_week_are_credited(self):
        task = self.task(deadline=moment(30))
        self.existing(task, moment(23, 8), moment(23, 8, 50), week=date(2026, 11, 23))
        row = self.result()["report"][0]
        self.assertEqual((row["existing_minutes"], row["scheduled_minutes"]), (50, 70))

    def test_ongoing_session_only_credits_remaining_whole_minutes(self):
        task = self.task()
        self.existing(task, moment(16, 8), moment(16, 8, 50))
        result = self.result(now=moment(16, 8, 25) + timedelta(seconds=1))
        self.assertEqual(result["report"][0]["existing_minutes"], 24)
        self.assertEqual(result["report"][0]["scheduled_minutes"], 96)
        self.assertEqual(result["sessions"][0][1], moment(16, 9))

    def test_past_sessions_do_not_complete_work_but_still_use_daily_budget(self):
        task = self.task()
        self.existing(task, moment(16, 8), moment(16, 8, 50))
        self.preference(max_daily_minutes=90)
        row = self.result(now=moment(16, 9))["report"][0]
        self.assertEqual((row["existing_minutes"], row["scheduled_minutes"]), (0, 40))

    def test_existing_unsplittable_partial_allocation_is_not_fragmented_again(self):
        task = self.task(can_split=False)
        self.existing(task, moment(16, 8), moment(16, 8, 50))
        result = self.result()
        self.assertEqual(result["sessions"], [])
        self.assertIn("rà soát", result["report"][0]["reason"])

    def test_breaks_across_days_apply_to_new_and_existing_sessions(self):
        self.preference(study_days=[0, 1], study_end=time(9), max_daily_minutes=60, break_minutes=1440)
        task = self.task(deadline=moment(18), remaining_minutes=60)
        result = self.result()
        self.assertEqual(result["sessions"], [
            (task.pk, moment(16, 8), moment(16, 8, 50)),
            (task.pk, moment(17, 8, 50), moment(17, 9)),
        ])
        self.existing(task, moment(15, 8), moment(15, 8, 50), week=date(2026, 11, 9))
        result = self.result()
        self.assertEqual(result["sessions"][0][1], moment(16, 8, 50))
        days = build_week(self.owner, MONDAY, self.preferences, now=moment(15))
        self.assertEqual(days[0]["free"][0]["start_label"], "08:50")

    def test_preview_is_deterministic_does_not_reserve_calendar_or_change_remaining(self):
        task = self.task()
        before = build_week(self.owner, MONDAY, self.preferences)
        plan = create_draft(self.owner, MONDAY)
        self.assertEqual(before, build_week(self.owner, MONDAY, self.preferences))
        self.assertEqual(self.result(), self.result())
        task.refresh_from_db()
        self.assertEqual(task.remaining_minutes, 120)
        self.assertIsNone(plan.applied_at)
        self.assertEqual(plan.sessions.count(), 3)

    def test_apply_is_idempotent_and_shows_sessions_on_calendar(self):
        task = self.task()
        plan = create_draft(self.owner, MONDAY)
        self.assertTrue(apply_plan(self.owner, plan.pk)[1])
        self.assertFalse(apply_plan(self.owner, plan.pk)[1])
        days = build_week(self.owner, MONDAY, self.preferences)
        self.assertEqual(len([item for item in days[0]["items"] if item["kind"] == "study"]), 3)
        self.assertEqual(days[0]["capacity_minutes"], 60)
        self.assertEqual(days[0]["free"][0]["start_label"], "10:30")
        task.refresh_from_db()
        self.assertEqual(task.remaining_minutes, 120)
        self.assertEqual(self.result()["sessions"], [])

    def test_changing_inputs_rejects_stale_preview_and_rolls_back_apply(self):
        task = self.task()
        changes = [
            lambda: Task.objects.filter(pk=task.pk).update(remaining_minutes=100),
            lambda: StudyPreference.objects.filter(owner=self.owner).update(break_minutes=20),
            lambda: BusyEvent.objects.create(owner=self.owner, title="Mới", starts_at=moment(16, 10), ends_at=moment(16, 11)),
            lambda: self.task(title="Thêm việc"),
        ]
        for change in changes:
            plan = create_draft(self.owner, MONDAY)
            change()
            with self.assertRaises(PlanError):
                apply_plan(self.owner, plan.pk)
            plan.refresh_from_db()
            self.assertIsNone(plan.applied_at)

    def test_applying_one_draft_invalidates_other_overlapping_draft(self):
        self.task()
        first, second = create_draft(self.owner, MONDAY), create_draft(self.owner, MONDAY)
        apply_plan(self.owner, first.pk)
        with self.assertRaises(PlanError):
            apply_plan(self.owner, second.pk)
        second.refresh_from_db()
        self.assertIsNone(second.applied_at)

    def test_expired_preview_and_empty_preview_cannot_be_applied(self):
        with self.assertRaises(PlanError):
            apply_plan(self.owner, create_draft(self.owner, MONDAY).pk)
        self.task()
        plan = create_draft(self.owner, MONDAY)
        with self.assertRaises(PlanError):
            apply_plan(self.owner, plan.pk, now=moment(16, 8) + timedelta(seconds=1))
        plan.refresh_from_db()
        self.assertIsNone(plan.applied_at)

    def test_apply_service_rejects_foreign_owner(self):
        self.task()
        plan = create_draft(self.owner, MONDAY)
        with self.assertRaises(StudyPlan.DoesNotExist):
            apply_plan(self.other, plan.pk)

    def test_session_validation_ownership_deadline_week_and_database_time_constraint(self):
        task = self.task()
        plan = create_draft(self.owner, MONDAY)
        session = plan.sessions.first()
        session.full_clean()
        for changes in ({"owner": self.other}, {"ends_at": moment(16, 13)},
                        {"starts_at": moment(17, 8), "ends_at": moment(17, 9)},
                        {"starts_at": moment(15, 8), "ends_at": moment(15, 9)}):
            candidate = StudySession(owner=self.owner, plan=plan, task=task,
                                     starts_at=moment(16, 8), ends_at=moment(16, 9))
            for field, value in changes.items():
                setattr(candidate, field, value)
            with self.assertRaises(ValidationError):
                candidate.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            StudySession.objects.create(owner=self.owner, plan=plan, task=task,
                                        starts_at=moment(16, 9), ends_at=moment(16, 8))
        plan.week_start = date(2026, 11, 17)
        with self.assertRaises(ValidationError):
            plan.full_clean()

    def test_deleting_task_removes_sessions_but_preserves_material(self):
        task = self.task()
        material = Material.objects.create(owner=self.owner, task=task, title="Link", url="https://example.com")
        plan = create_draft(self.owner, MONDAY)
        apply_plan(self.owner, plan.pk)
        task.delete()
        self.assertEqual(plan.sessions.count(), 0)
        material.refresh_from_db()
        self.assertIsNone(material.task_id)

    def test_forms_normalize_week_and_reject_past_and_invalid_dates(self):
        form = PlanWeekForm({"week": "2026-11-18"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["week"], MONDAY)
        for value in ("2026-11-01", "bad", "9999-12-31"):
            self.assertFalse(PlanWeekForm({"week": value}).is_valid())

    def test_views_preview_apply_history_and_get_do_not_write(self):
        task = self.task()
        self.client.force_login(self.owner)
        generate = reverse("planner:plan_generate")
        response = self.client.get(generate)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(StudyPlan.objects.count(), 0)
        response = self.client.post(generate, {"week": "2026-11-18", "owner": self.other.pk})
        plan = StudyPlan.objects.get()
        self.assertEqual((plan.owner, plan.week_start), (self.owner, MONDAY))
        detail, apply = reverse("planner:plan_detail", args=[plan.pk]), reverse("planner:plan_apply", args=[plan.pk])
        self.assertRedirects(response, detail)
        self.assertContains(self.client.get(detail), "Bản xem trước · chưa có trên lịch")
        self.assertEqual(self.client.get(apply).status_code, 405)
        self.assertRedirects(self.client.post(apply, {"owner": self.other.pk}), "/planner/?week=2026-11-16")
        self.assertContains(self.client.get(generate), "Đã áp dụng")
        self.assertEqual(self.client.post(apply).status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.remaining_minutes, 120)

    def test_views_auth_ownership_and_csrf(self):
        self.task()
        plan = create_draft(self.owner, MONDAY)
        detail, apply = reverse("planner:plan_detail", args=[plan.pk]), reverse("planner:plan_apply", args=[plan.pk])
        for url in (reverse("planner:plan_generate"), detail):
            self.assertEqual(self.client.get(url).status_code, 302)
        self.assertEqual(self.client.post(apply).status_code, 302)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(detail).status_code, 404)
        self.assertEqual(self.client.post(apply).status_code, 404)
        self.assertNotContains(self.client.get(reverse("planner:plan_generate")), "16/11/2026")
        secure = Client(enforce_csrf_checks=True)
        secure.force_login(self.owner)
        for url in (reverse("planner:plan_generate"), apply):
            self.assertEqual(secure.post(url, {"week": "2026-11-16"}).status_code, 403)

    def test_recent_history_is_newest_first_and_limited_to_ten(self):
        plans = [create_draft(self.owner, MONDAY) for _ in range(12)]
        create_draft(self.other, MONDAY)
        self.client.force_login(self.owner)
        response = self.client.get(reverse("planner:plan_generate"))
        self.assertEqual([p.pk for p in response.context["recent_plans"]], [p.pk for p in reversed(plans[2:])])

    def test_invalid_and_stale_requests_render_useful_errors_without_applying(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("planner:plan_generate"), {"week": "bad"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(StudyPlan.objects.count(), 0)
        task = self.task()
        plan = create_draft(self.owner, MONDAY)
        task.remaining_minutes = 60
        task.save()
        response = self.client.post(reverse("planner:plan_apply", args=[plan.pk]))
        self.assertContains(response, "Hãy tạo bản xem trước mới", status_code=409)
        self.assertNotContains(response, "Áp dụng vào lịch tuần", status_code=409)
        plan.refresh_from_db()
        self.assertIsNone(plan.applied_at)
