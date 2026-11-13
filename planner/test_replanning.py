from datetime import date, time, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from studies.models import Task

from .models import BusyEvent, StudyPlan, StudyPreference, StudySession
from .services.alerts import build_alerts
from .services.availability import at_time, build_week
from .services.scheduling import PlanError, apply_plan, calculate_schedule, create_draft
from .services.sessions import move_session, record_session, set_session_lock

MONDAY = date(2026, 11, 16)


def moment(day, hour=0, minute=0):
    return at_time(date(2026, 11, day), time(hour, minute))


class ReplanningTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="replan_owner")
        cls.other = get_user_model().objects.create_user(username="replan_other")
        cls.preference = StudyPreference.objects.create(
            owner=cls.owner, study_days=[0, 1], study_start=time(8), study_end=time(12),
            max_daily_minutes=240, session_minutes=50, break_minutes=10,
        )

    def setUp(self):
        self.clock = patch("planner.services.scheduling.timezone.now", return_value=moment(15))
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.client.force_login(self.owner)

    def task(self, **kwargs):
        values = {"owner": self.owner, "title": "Việc cần học", "deadline": moment(17, 12),
                  "estimated_minutes": 120, "remaining_minutes": 120}
        return Task.objects.create(**{**values, **kwargs})

    def session(self, task=None, start=None, end=None, **kwargs):
        task = task or self.task()
        start, end = start or moment(16, 8), end or moment(16, 8, 50)
        monday = start.date() - timedelta(days=start.date().weekday())
        plan = StudyPlan.objects.create(owner=task.owner, week_start=monday, applied_at=moment(15))
        return StudySession.objects.create(owner=task.owner, plan=plan, task=task, starts_at=start, ends_at=end, **kwargs)

    def replace_draft(self, **kwargs):
        return create_draft(self.owner, MONDAY, mode=StudyPlan.Mode.REPLACE, **kwargs)

    def test_replacement_only_targets_future_automatic_unlocked_planned_sessions_in_week(self):
        task = self.task(remaining_minutes=600, deadline=moment(30))
        auto = self.session(task)
        protected = [
            self.session(task, moment(16, 9), moment(16, 9, 50), is_locked=True),
            self.session(task, moment(16, 10), moment(16, 10, 50), is_manual=True),
            self.session(task, moment(16, 11), moment(16, 11, 50), status=StudySession.Status.DONE),
            self.session(task, moment(16, 12), moment(16, 12, 50), status=StudySession.Status.CANCELLED),
            self.session(task, moment(23, 8), moment(23, 8, 50)),
            self.session(self.task(owner=self.other)),
        ]
        protected_statuses = {s.pk: s.status for s in protected}
        plan = self.replace_draft()
        self.assertEqual(plan.replacement_ids, [auto.pk])
        for session in protected:
            session.refresh_from_db()
            self.assertEqual(session.status, protected_statuses[session.pk])
        auto.refresh_from_db()
        self.assertEqual(auto.status, StudySession.Status.PLANNED)

    def test_ongoing_and_started_sessions_are_preserved(self):
        ongoing = self.session()
        for now in (moment(16, 8), moment(16, 8, 25), moment(16, 9)):
            self.assertNotIn(ongoing.pk, self.replace_draft(now=now).replacement_ids)

    def test_add_mode_keeps_all_applied_sessions(self):
        old = self.session()
        plan = create_draft(self.owner, MONDAY)
        self.assertEqual(plan.replacement_ids, [])
        self.assertEqual(plan.mode, StudyPlan.Mode.ADD)
        self.assertEqual(plan.report[0]["existing_minutes"], old.duration_minutes)

    def test_preview_does_not_cancel_old_sessions_or_change_calendar(self):
        old = self.session()
        before = build_week(self.owner, MONDAY, self.preference)
        self.replace_draft()
        old.refresh_from_db()
        self.assertEqual(old.status, StudySession.Status.PLANNED)
        self.assertEqual(before, build_week(self.owner, MONDAY, self.preference))

    def test_apply_replaces_old_sessions_atomically_and_keeps_history(self):
        old = self.session()
        BusyEvent.objects.create(owner=self.owner, title="Ca làm mới", starts_at=moment(16, 8), ends_at=moment(16, 10))
        plan = self.replace_draft()
        self.assertEqual(plan.sessions.first().starts_at, moment(16, 10))
        apply_plan(self.owner, plan.pk)
        old.refresh_from_db()
        self.assertEqual(old.status, StudySession.Status.CANCELLED)
        self.assertTrue(StudySession.objects.filter(pk=old.pk).exists())
        days = build_week(self.owner, MONDAY, self.preference)
        self.assertNotIn(old.pk, [item["session"].pk for d in days for item in d["items"] if item["kind"] == "study"])
        self.assertFalse(apply_plan(self.owner, plan.pk)[1])

    def test_replacement_can_apply_with_zero_new_sessions_when_work_is_done(self):
        task = self.task(status=Task.Status.DONE, remaining_minutes=0)
        old = self.session(task)
        plan = self.replace_draft()
        self.assertEqual(plan.sessions.count(), 0)
        self.assertContains(self.client.get(reverse("planner:plan_detail", args=[plan.pk])), "Áp dụng vào lịch tuần")
        apply_plan(self.owner, plan.pk)
        old.refresh_from_db()
        self.assertEqual(old.status, StudySession.Status.CANCELLED)

    def test_lock_change_after_preview_rejects_apply_without_cancelling_old(self):
        old = self.session()
        plan = self.replace_draft()
        set_session_lock(self.owner, old.pk, True)
        with self.assertRaises(PlanError):
            apply_plan(self.owner, plan.pk)
        old.refresh_from_db()
        plan.refresh_from_db()
        self.assertEqual(old.status, StudySession.Status.PLANNED)
        self.assertIsNone(plan.applied_at)

    def test_time_passing_into_old_session_invalidates_replacement(self):
        old = self.session()
        plan = self.replace_draft()
        with self.assertRaises(PlanError):
            apply_plan(self.owner, plan.pk, now=moment(16, 8))
        old.refresh_from_db()
        self.assertEqual(old.status, StudySession.Status.PLANNED)

    def test_moving_marks_manual_and_keeps_it_when_replanning(self):
        old = self.session()
        moved = move_session(self.owner, old.pk, moment(16, 10), moment(16, 10, 50))
        self.assertTrue(moved.is_manual)
        self.assertNotIn(old.pk, self.replace_draft().replacement_ids)
        old.refresh_from_db()
        self.assertEqual(old.starts_at, moment(16, 10))

    def test_move_rejects_busy_overlap_with_weekly_overnight_event(self):
        old = self.session()
        BusyEvent.objects.create(owner=self.owner, title="Ca đêm", starts_at=moment(8, 22), ends_at=moment(9, 10), repeat_weekly=True)
        with self.assertRaisesMessage(PlanError, "trùng lịch bận"):
            move_session(self.owner, old.pk, moment(16, 9), moment(16, 9, 50))
        old.refresh_from_db()
        self.assertFalse(old.is_manual)

    def test_move_rejects_overlap_or_insufficient_break_but_allows_exact_break(self):
        old = self.session()
        self.session(self.task(), moment(16, 10), moment(16, 10, 50))
        for start, end in ((moment(16, 10, 10), moment(16, 11)),
                           (moment(16, 9, 1), moment(16, 9, 51))):
            with self.assertRaisesMessage(PlanError, "thời gian nghỉ"):
                move_session(self.owner, old.pk, start, end)
        move_session(self.owner, old.pk, moment(16, 9), moment(16, 9, 50))

    def test_move_rejects_outside_window_deadline_week_or_cross_day(self):
        old = self.session()
        cases = [(moment(16, 7), moment(16, 7, 50)),
                 (moment(16, 12), moment(16, 12, 50)),
                 (moment(18, 8), moment(18, 8, 50)),
                 (moment(23, 8), moment(23, 8, 50)),
                 (moment(16, 23), moment(17, 1)),
                 (moment(16, 10), moment(16, 9)),
                 (moment(16, 9) + timedelta(seconds=1), moment(16, 9, 50))]
        for start, end in cases:
            with self.subTest(start=start, end=end), self.assertRaises(PlanError):
                move_session(self.owner, old.pk, start, end)

    def test_move_rejects_past_started_locked_or_finalized_session(self):
        old = self.session()
        for now in (moment(16, 8), moment(16, 9)):
            with self.assertRaises(PlanError):
                move_session(self.owner, old.pk, moment(16, 10), moment(16, 10, 50), now=now)
        set_session_lock(self.owner, old.pk, True)
        with self.assertRaisesMessage(PlanError, "Mở khóa"):
            move_session(self.owner, old.pk, moment(16, 10), moment(16, 10, 50))
        set_session_lock(self.owner, old.pk, False)
        record_session(self.owner, old.pk, StudySession.Status.CANCELLED, 120)
        with self.assertRaises(PlanError):
            move_session(self.owner, old.pk, moment(16, 10), moment(16, 10, 50))

    def test_move_rejects_daily_budget_and_overallocation(self):
        old = self.session()
        StudyPreference.objects.filter(owner=self.owner).update(max_daily_minutes=50)
        self.session(self.task(), moment(17, 8), moment(17, 8, 50))
        with self.assertRaisesMessage(PlanError, "giới hạn ngày"):
            move_session(self.owner, old.pk, moment(17, 10), moment(17, 10, 50))
        with self.assertRaisesMessage(PlanError, "thời lượng công việc còn lại"):
            move_session(self.owner, old.pk, moment(16, 8), moment(16, 10, 30))

    def test_move_unsplittable_task_requires_whole_remaining_duration(self):
        old = self.session(self.task(can_split=False))
        with self.assertRaisesMessage(PlanError, "không chia buổi"):
            move_session(self.owner, old.pk, moment(16, 8), moment(16, 8, 50))
        move_session(self.owner, old.pk, moment(16, 8), moment(16, 10))

    def test_lock_is_explicit_and_idempotent_not_a_toggle(self):
        old = self.session()
        set_session_lock(self.owner, old.pk, True)
        set_session_lock(self.owner, old.pk, True)
        old.refresh_from_db()
        self.assertTrue(old.is_locked)
        set_session_lock(self.owner, old.pk, False)
        old.refresh_from_db()
        self.assertFalse(old.is_locked)

    def test_record_done_updates_absolute_remaining_and_status_without_automatic_subtraction(self):
        old = self.session()
        record_session(self.owner, old.pk, StudySession.Status.DONE, 100, now=moment(16, 9))
        old.refresh_from_db()
        old.task.refresh_from_db()
        self.assertEqual(old.status, StudySession.Status.DONE)
        self.assertEqual((old.task.remaining_minutes, old.task.status), (100, Task.Status.IN_PROGRESS))
        with self.assertRaises(PlanError):
            record_session(self.owner, old.pk, StudySession.Status.DONE, 50, now=moment(16, 9))
        old.task.refresh_from_db()
        self.assertEqual(old.task.remaining_minutes, 100)

    def test_record_zero_completes_task_and_preserves_done_session_on_replan(self):
        old = self.session(is_locked=True)
        record_session(self.owner, old.pk, StudySession.Status.DONE, 0, now=moment(16, 9))
        old.task.refresh_from_db()
        self.assertEqual(old.task.status, Task.Status.DONE)
        self.assertNotIn(old.pk, self.replace_draft(now=moment(16, 9)).replacement_ids)

    def test_record_cannot_complete_future_but_can_cancel_without_changing_task(self):
        old = self.session()
        with self.assertRaises(PlanError):
            record_session(self.owner, old.pk, StudySession.Status.DONE, 0)
        with self.assertRaisesMessage(PlanError, "không đổi tiến độ"):
            record_session(self.owner, old.pk, StudySession.Status.CANCELLED, 0)
        record_session(self.owner, old.pk, StudySession.Status.CANCELLED, 120)
        old.task.refresh_from_db()
        self.assertEqual(old.task.remaining_minutes, 120)
        self.assertEqual(build_week(self.owner, MONDAY, self.preference)[0]["capacity_minutes"], 240)

    def test_cancel_locked_session_is_rejected_and_invalid_input_has_no_effect(self):
        old = self.session(is_locked=True)
        for result, remaining in ((StudySession.Status.CANCELLED, 120), ("bad", 120),
                                  (StudySession.Status.DONE, -1), (StudySession.Status.DONE, 2**63)):
            with self.assertRaises(PlanError):
                record_session(self.owner, old.pk, result, remaining)
        old.refresh_from_db()
        self.assertEqual(old.status, StudySession.Status.PLANNED)

    def test_done_sessions_block_time_and_budget_but_are_not_future_credit(self):
        old = self.session(status=StudySession.Status.DONE)
        result = calculate_schedule(self.owner, MONDAY, now=moment(16, 8, 30))
        self.assertEqual(result["report"][0]["existing_minutes"], 0)
        self.assertEqual(result["sessions"][0][1], moment(16, 9))
        self.assertNotIn(old.pk, result["replacement_ids"])

    def test_progress_change_invalidates_preview_and_replan_uses_new_remaining(self):
        old = self.session()
        plan = self.replace_draft()
        self.client.post(reverse("studies:task_progress", args=[old.task_id]), {"status": "in_progress", "remaining_minutes": 60})
        with self.assertRaises(PlanError):
            apply_plan(self.owner, plan.pk)
        new = self.replace_draft()
        self.assertEqual(sum(s.duration_minutes for s in new.sessions.all()), 60)

    def test_alerts_overdue_due_soon_missing_future_credit_and_completed_exclusion(self):
        overdue = self.task(title="Quá hạn", deadline=moment(14))
        due = self.task(title="Sắp đến hạn")
        self.session(due)
        self.task(title="Đã xong", status=Task.Status.DONE, remaining_minutes=0)
        self.task(title="Xa", deadline=moment(30))
        rows = build_alerts(self.owner)["task_alerts"]
        self.assertEqual([r["task"].pk for r in rows], [overdue.pk, due.pk])
        self.assertEqual((rows[0]["overdue"], rows[1]["missing"]), (True, 70))

    def test_alerts_detect_busy_deadline_window_budget_break_and_excess_minutes(self):
        old = self.session()
        BusyEvent.objects.create(owner=self.owner, title="Bận mới", starts_at=moment(16, 8), ends_at=moment(16, 9))
        self.session(self.task(), moment(16, 8, 40), moment(16, 9, 30))
        StudyPreference.objects.filter(owner=self.owner).update(study_days=[], max_daily_minutes=50)
        Task.objects.filter(pk=old.task_id).update(deadline=moment(16, 8, 30), remaining_minutes=10)
        row = next(r for r in build_alerts(self.owner)["conflicts"] if r["session"].pk == old.pk)
        for fragment in ("deadline", "khung giờ", "lịch bận", "thời gian nghỉ", "giới hạn ngày", "thời lượng công việc"):
            self.assertTrue(any(fragment in reason for reason in row["reasons"]), row)

    def test_alerts_include_unrecorded_recent_twenty_and_respect_owner_and_horizon(self):
        for i in range(22):
            self.session(start=moment(9, 8) + timedelta(minutes=i), end=moment(9, 9) + timedelta(minutes=i))
        self.session(self.task(owner=self.other), moment(10, 8), moment(10, 9))
        self.session(self.task(deadline=moment(30)), moment(23, 7), moment(23, 7, 50))
        rows = build_alerts(self.owner)
        self.assertEqual((rows["unrecorded_count"], len(rows["unrecorded"])), (22, 20))
        self.assertGreater(rows["unrecorded"][0].ends_at, rows["unrecorded"][-1].ends_at)
        self.assertEqual(rows["conflicts"], [])

    def test_alerts_flag_completed_task_reservation_and_cancelled_not_included(self):
        old = self.session(self.task(status=Task.Status.DONE, remaining_minutes=0))
        self.assertIn("hoàn thành", build_alerts(self.owner)["conflicts"][0]["reasons"][0])
        record_session(self.owner, old.pk, StudySession.Status.CANCELLED, 0)
        self.assertEqual(build_alerts(self.owner)["conflicts"], [])

    def test_progress_view_owner_validation_and_done_normalization(self):
        task = self.task()
        url = reverse("studies:task_progress", args=[task.pk])
        self.assertContains(self.client.get(url), task.title)
        self.assertEqual(self.client.post(url, {"status": "in_progress", "remaining_minutes": 0}).status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.remaining_minutes, 120)
        self.assertEqual(self.client.post(url, {"status": "done", "remaining_minutes": 120, "owner": self.other.pk}).status_code, 302)
        task.refresh_from_db()
        self.assertEqual((task.status, task.remaining_minutes, task.owner), (Task.Status.DONE, 0, self.owner))
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(url, {"status": "done", "remaining_minutes": 0}).status_code, 404)

    def test_session_views_modify_only_allowed_fields_and_show_final_status(self):
        old = self.session()
        move = reverse("planner:session_move", args=[old.pk])
        self.assertEqual(self.client.get(move).status_code, 200)
        self.assertEqual(self.client.post(move, {"starts_at": "2026-11-16T10:00", "ends_at": "2026-11-16T10:50", "owner": self.other.pk, "status": "done", "task": self.task(owner=self.other).pk}).status_code, 302)
        old.refresh_from_db()
        self.assertEqual((old.owner, old.status, old.is_manual), (self.owner, StudySession.Status.PLANNED, True))
        lock = reverse("planner:session_lock", args=[old.pk])
        self.assertEqual(self.client.get(lock).status_code, 405)
        self.assertEqual(self.client.post(lock, {"locked": "true"}).status_code, 302)
        self.assertContains(self.client.post(move, {"starts_at": "2026-11-16T11:00", "ends_at": "2026-11-16T11:50"}), "Mở khóa")
        self.client.post(lock, {"locked": "false"})
        record = reverse("planner:session_record", args=[old.pk])
        self.assertEqual(self.client.post(record, {"result": "cancelled", "remaining_minutes": 120}).status_code, 302)
        self.assertContains(self.client.post(record, {"result": "done", "remaining_minutes": 0}), "không thể thực hiện lại")

    def test_session_views_reject_foreign_and_draft_sessions_and_require_login(self):
        old = self.session()
        draft = create_draft(self.owner, MONDAY).sessions.first()
        for name in ("session_move", "session_record", "session_lock"):
            url = reverse(f"planner:{name}", args=[old.pk])
            self.client.logout()
            self.assertEqual(self.client.post(url).status_code, 302)
            self.client.force_login(self.other)
            self.assertEqual(self.client.post(url).status_code, 404)
            self.client.force_login(self.owner)
            self.assertEqual(self.client.post(reverse(f"planner:{name}", args=[draft.pk])).status_code, 404)

    def test_csrf_on_all_new_mutations_and_no_get_writes(self):
        old = self.session()
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        for name in ("session_move", "session_record", "session_lock"):
            self.assertEqual(client.post(reverse(f"planner:{name}", args=[old.pk])).status_code, 403)
        self.assertEqual(client.post(reverse("studies:task_progress", args=[old.task_id])).status_code, 403)
        for name in ("session_move", "session_record"):
            self.client.get(reverse(f"planner:{name}", args=[old.pk]))
        self.assertEqual(self.client.get(reverse("planner:alerts")).status_code, 200)
        old.refresh_from_db()
        self.assertEqual((old.status, old.is_manual, old.is_locked), (StudySession.Status.PLANNED, False, False))

    def test_generate_replace_from_form_and_preview_shows_old_sessions(self):
        old = self.session()
        response = self.client.post(reverse("planner:plan_generate"), {"week": "2026-11-18", "mode": "replace"})
        plan = StudyPlan.objects.filter(applied_at__isnull=True).get()
        self.assertEqual((plan.mode, plan.replacement_ids), (StudyPlan.Mode.REPLACE, [old.pk]))
        self.assertRedirects(response, reverse("planner:plan_detail", args=[plan.pk]))
        self.assertContains(self.client.get(response.url), "Sẽ hủy 1 buổi cũ")
        response = self.client.post(reverse("planner:plan_generate"), {"week": "2026-11-16", "mode": "bad"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(StudyPlan.objects.filter(applied_at__isnull=True).count(), 1)
