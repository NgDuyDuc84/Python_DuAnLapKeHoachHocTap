from datetime import date, time, timedelta
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from focus.models import StudyLog
from studies.models import Material, Subject, Task

from .models import BusyEvent, StudyPlan, StudyPreference, StudySession
from .services.availability import at_time, build_week


MONDAY = date(2026, 11, 16)


def clock(hour, minute=0, day=MONDAY):
    return at_time(day, time(hour, minute))


class CalendarPeriodTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user("period-owner")

    def week(self):
        return build_week(self.owner, MONDAY, StudyPreference(owner=self.owner), now=clock(0))

    def test_events_crossing_periods_are_clipped_without_changing_availability(self):
        BusyEvent.objects.create(owner=self.owner, title="Noon class", starts_at=clock(11), ends_at=clock(13))
        BusyEvent.objects.create(owner=self.owner, title="Evening class", starts_at=clock(17), ends_at=clock(19))
        day = self.week()[0]
        morning, afternoon, evening = day["periods"]
        self.assertEqual([p["label"] for p in day["periods"]], ["Sáng", "Chiều", "Tối"])
        self.assertEqual([(i["start_label"], i["end_label"]) for i in morning["items"]], [("11:00", "12:00")])
        self.assertEqual([(i["start_label"], i["end_label"]) for i in afternoon["items"]], [("12:00", "13:00"), ("17:00", "18:00")])
        self.assertEqual([(i["start_label"], i["end_label"]) for i in evening["items"]], [("18:00", "19:00")])
        self.assertEqual(len(day["items"]), 2)
        self.assertEqual([(i["start_label"], i["end_label"]) for i in day["free"]],
                         [("08:00", "11:00"), ("13:00", "17:00"), ("19:00", "22:00")])
        self.assertEqual(day["capacity_minutes"], 240)

    def test_deadline_at_noon_and_evening_boundary_appears_exactly_once(self):
        for hour in (0, 12, 18):
            Task.objects.create(owner=self.owner, title=f"Deadline {hour}", deadline=clock(hour),
                                estimated_minutes=20, remaining_minutes=20)
        periods = self.week()[0]["periods"]
        self.assertEqual([[i["task"].title for i in p["items"]] for p in periods],
                         [["Deadline 0"], ["Deadline 12"], ["Deadline 18"]])

    def test_overnight_busy_event_spans_evening_and_next_morning(self):
        BusyEvent.objects.create(owner=self.owner, title="Night shift", starts_at=clock(23),
                                 ends_at=clock(2, day=MONDAY + timedelta(days=1)))
        days = self.week()
        self.assertEqual(days[0]["periods"][2]["items"][0]["end_label"], "24:00")
        self.assertEqual(days[1]["periods"][0]["items"][0]["start_label"], "00:00")
        self.assertEqual(days[1]["periods"][0]["items"][0]["end_label"], "02:00")

    def test_applied_session_spans_periods_and_excludes_drafts_cancelled_and_foreign_data(self):
        task = Task.objects.create(owner=self.owner, title="Study across noon", deadline=clock(22),
                                   estimated_minutes=60, remaining_minutes=60)
        for applied, status in [(True, "planned"), (False, "planned"), (True, "cancelled")]:
            plan = StudyPlan.objects.create(owner=self.owner, week_start=MONDAY, applied_at=clock(0) if applied else None)
            StudySession.objects.create(owner=self.owner, task=task, plan=plan, status=status,
                                        starts_at=clock(11, 30), ends_at=clock(12, 30))
        other = get_user_model().objects.create_user("period-other")
        BusyEvent.objects.create(owner=other, title="Other private", starts_at=clock(9), ends_at=clock(10))
        day = self.week()[0]
        self.assertEqual([len([i for i in p["items"] if i["kind"] == "study"]) for p in day["periods"]], [1, 1, 0])
        self.assertEqual(day["periods"][0]["items"][0]["end_label"], "12:00")
        self.assertEqual(day["periods"][1]["items"][0]["start_label"], "12:00")


class StudySidebarTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user("workspace-owner")
        cls.other = get_user_model().objects.create_user("workspace-other")
        cls.subject = Subject.objects.create(owner=cls.owner, name="Own Python")
        cls.task = Task.objects.create(owner=cls.owner, subject=cls.subject, title="Own report", deadline=clock(22),
                                       estimated_minutes=60, remaining_minutes=60)
        cls.material = Material.objects.create(owner=cls.owner, title="Own reference", url="https://docs.python.org/3/")
        cls.private = {}
        cls.private["subjects"] = Subject.objects.create(owner=cls.other, name="Private subject")
        cls.private["tasks"] = Task.objects.create(owner=cls.other, title="Private task", deadline=clock(22),
                                                  estimated_minutes=30, remaining_minutes=30)
        cls.private["materials"] = Material.objects.create(owner=cls.other, title="Private material", url="https://example.test/")

    def setUp(self):
        self.client.force_login(self.owner)

    def url(self, panel="tasks", **kwargs):
        return reverse("planner:week") + "?" + urlencode({"week": "2026-11-18", "panel": panel, **kwargs})

    def task_data(self, **kwargs):
        return {"operation": "save", "title": "New task", "subject": self.subject.pk,
                "deadline": "2026-11-19T22:00", "priority": "3", "estimated_minutes": "60",
                "can_split": "on", "status": "todo", **kwargs}

    def test_all_panels_live_beside_selected_week_and_show_only_owned_data(self):
        for panel, own in [("subjects", self.subject), ("tasks", self.task), ("materials", self.material)]:
            response = self.client.get(self.url(panel))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context["week_start"], MONDAY)
            self.assertContains(response, str(own))
            self.assertNotContains(response, str(self.private[panel]))
            self.assertContains(response, 'class="calendar-main"')
            self.assertNotContains(response, "Cách sử dụng")
        self.assertEqual(self.client.get(reverse("planner:week"), {"panel": "subjects"}).status_code, 200)

    def test_create_each_object_ignores_forged_owner_and_preserves_week(self):
        cases = [
            ("subjects", Subject, {"name": "New subject", "color": "#176b58"}),
            ("tasks", Task, self.task_data()),
            ("materials", Material, {"title": "New material", "url": "https://docs.python.org/3/", "task": self.task.pk}),
        ]
        for panel, model, data in cases:
            response = self.client.post(self.url(panel), {**data, "operation": "save", "owner": self.other.pk})
            self.assertRedirects(response, f"/planner/?week=2026-11-16&panel={panel}#hoc-tap")
            self.assertEqual(model.objects.latest("pk").owner, self.owner)
        self.assertContains(self.client.get(self.url()), "New task")

    def test_edit_progress_uses_existing_task_rules_and_refreshes_calendar(self):
        response = self.client.post(self.url(), self.task_data(object_id=str(self.task.pk), title="Finished report",
                                                              status="done", remaining_minutes="60"))
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual((self.task.status, self.task.remaining_minutes), ("done", 0))
        response = self.client.get(self.url())
        self.assertContains(response, "Finished report")
        self.assertContains(response, "Đã hoàn thành")

    def test_invalid_form_keeps_bound_values_errors_and_calendar(self):
        response = self.client.post(self.url(), self.task_data(estimated_minutes="0"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("estimated_minutes", response.context["sidebar_form"].errors)
        self.assertEqual(response.context["sidebar_form"]["title"].value(), "New task")
        self.assertEqual(response.context["week_start"], MONDAY)
        self.assertEqual(len(response.context["days"]), 7)
        self.assertEqual(Task.objects.filter(owner=self.owner).count(), 1)

    def test_foreign_object_cannot_be_read_edited_or_deleted(self):
        for panel, obj in self.private.items():
            for action in ("edit", "delete"):
                self.assertEqual(self.client.get(self.url(panel, action=action, id=obj.pk)).status_code, 404)
            for operation in ("save", "delete"):
                self.assertEqual(self.client.post(self.url(panel), {"operation": operation, "object_id": obj.pk}).status_code, 404)
            obj.refresh_from_db()

    def test_foreign_links_and_unsafe_material_urls_are_rejected(self):
        response = self.client.post(self.url(), self.task_data(subject=self.private["subjects"].pk))
        self.assertIn("subject", response.context["sidebar_form"].errors)
        response = self.client.post(self.url("materials"), {"operation": "save", "title": "Unsafe", "url": "javascript:alert(1)"})
        self.assertIn("url", response.context["sidebar_form"].errors)
        self.assertFalse(Material.objects.filter(title="Unsafe").exists())

    def test_delete_requires_post_and_keeps_existing_cascade_rules(self):
        plan = StudyPlan.objects.create(owner=self.owner, week_start=MONDAY, applied_at=clock(0))
        StudySession.objects.create(owner=self.owner, plan=plan, task=self.task, starts_at=clock(9), ends_at=clock(10))
        self.material.task = self.task
        self.material.save()
        log = StudyLog.objects.create(owner=self.owner, task=self.task, task_title=self.task.title,
                                      studied_on=MONDAY - timedelta(days=1), minutes=25)
        self.client.get(self.url(action="delete", id=self.task.pk))
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())
        response = self.client.post(self.url(), {"operation": "delete", "object_id": self.task.pk})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(StudySession.objects.filter(task_id=self.task.pk).exists())
        self.material.refresh_from_db()
        log.refresh_from_db()
        self.assertIsNone(self.material.task_id)
        self.assertIsNone(log.task_id)
        self.assertEqual(log.task_title, "Own report")

    def test_search_pagination_keeps_week_and_does_not_expose_other_owner(self):
        for number in range(10):
            Subject.objects.create(owner=self.owner, name=f"Search {number}")
        response = self.client.get(self.url("subjects", q="Search", page=2))
        self.assertEqual(response.context["sidebar_page"].paginator.count, 10)
        self.assertEqual(len(response.context["sidebar_page"]), 2)
        self.assertContains(response, "week=2026-11-16&amp;panel=subjects")
        self.assertNotContains(response, "Private subject")

    def test_invalid_operations_and_ids_do_not_mutate_data(self):
        for pk in ("x", "-1", "9" * 50):
            self.assertEqual(self.client.get(self.url(action="edit", id=pk)).status_code, 404)
        for path, data in [(self.url("unknown"), {"operation": "save"}),
                           (self.url(), {"operation": "invalid"}),
                           (reverse("planner:week") + "?week=bad", self.task_data())]:
            self.assertEqual(self.client.post(path, data).status_code, 400)
        self.assertEqual(Task.objects.count(), 2)

    def test_csrf_and_login_are_required_for_sidebar_writes(self):
        anonymous = Client()
        self.assertEqual(anonymous.post(self.url(), self.task_data()).status_code, 302)
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.owner)
        self.assertEqual(strict.post(self.url(), self.task_data()).status_code, 403)
        strict.get(self.url(action="new"))
        response = strict.post(self.url(), {**self.task_data(), "csrfmiddlewaretoken": strict.cookies["csrftoken"].value})
        self.assertEqual(response.status_code, 302)
