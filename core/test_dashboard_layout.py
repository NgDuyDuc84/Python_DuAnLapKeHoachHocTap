from datetime import datetime, timedelta
from html.parser import HTMLParser
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from focus.models import FocusSession
from planner.models import StudyPlan, StudySession
from planner.services.alerts import build_alerts
from studies.models import Subject, Task

from .dashboard import build_dashboard


class FocusForms(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.forms = []
        self.current = None
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form" and attrs.get("action") == reverse("focus:home"):
            self.current = {}
        if tag == "input" and self.current is not None and "name" in attrs:
            self.current[attrs["name"]] = attrs.get("value", "")

    def handle_endtag(self, tag):
        if tag == "form" and self.current is not None:
            self.forms.append(self.current)
            self.current = None


class DashboardLayoutTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.now = timezone.make_aware(datetime(2026, 11, 17, 9))
        cls.user = get_user_model().objects.create_user("dashboard-learner", first_name="An")
        cls.new_user = get_user_model().objects.create_user("dashboard-new")
        cls.other = get_user_model().objects.create_user("dashboard-private")
        cls.subject = Subject.objects.create(owner=cls.user, name="Python", color="#228855")
        cls.task = Task.objects.create(owner=cls.user, subject=cls.subject, title="Bài thực hành socket",
                                      deadline=cls.now + timedelta(days=3), estimated_minutes=60, remaining_minutes=60)
        cls.plan = StudyPlan.objects.create(owner=cls.user, week_start=cls.now.date() - timedelta(days=1), applied_at=cls.now)
        Task.objects.create(owner=cls.other, title="Việc riêng tư", deadline=cls.now - timedelta(days=1),
                            estimated_minutes=10, remaining_minutes=10)

    def setUp(self):
        self.clock = patch("core.dashboard.timezone.now", return_value=self.now)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.client.force_login(self.user)

    def session(self, start, end, **changes):
        return StudySession.objects.create(owner=self.user, plan=self.plan, task=self.task,
                                           starts_at=start, ends_at=end, **changes)

    def test_new_user_gets_only_checklist_until_three_steps_are_complete(self):
        self.client.force_login(self.new_user)
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["action"]["kind"], "onboarding")
        self.assertNotContains(response, 'class="dashboard-metrics"')
        self.assertNotContains(response, 'class="dashboard-panels"')
        self.assertNotContains(response, 'class="dashboard-week"')
        self.assertContains(response, "Hôm nay chưa có buổi học nào.")
        Subject.objects.create(owner=self.new_user, name="Môn đầu tiên")
        Task.objects.create(owner=self.new_user, title="Việc xa hạn", deadline=self.now + timedelta(days=20),
                            estimated_minutes=30, remaining_minutes=30)
        response = self.client.get(reverse("core:home"))
        self.assertEqual([step["done"] for step in response.context["onboarding_steps"]], [True, True, False])
        self.assertEqual(response.context["action"]["kind"], "onboarding")
        StudyPlan.objects.create(owner=self.new_user, week_start=self.plan.week_start)
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.context["action"]["kind"], "ready")
        self.assertNotContains(response, 'class="onboarding-steps"')

    def test_unscheduled_task_and_running_focus_both_render_200(self):
        self.plan.delete()
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["action"]["kind"], "shortfall")
        self.assertContains(response, "Chưa có lịch")
        self.assertContains(response, "Còn 60 phút cần học")
        self.assertNotContains(response, "Việc riêng tư")
        self.assertNotContains(response, "Bước tiếp theo của bạn")
        self.assertNotContains(response, "Mở lịch học của bạn")
        self.assertContains(response, "Chào An")
        active = FocusSession.objects.create(owner=self.user, task=self.task, task_title=self.task.title, resumed_at=self.now)
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["action"]["kind"], "focus")
        self.assertContains(response, reverse("focus:session", args=[active.pk]))

    def test_start_forms_reuse_pomodoro_endpoint_csrf_and_request_keys(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.get(reverse("core:home"))
        forms = FocusForms(response.content.decode()).forms
        self.assertEqual(len(forms), 2)
        self.assertEqual(len({form["request_key"] for form in forms}), len(forms))
        for form in forms:
            self.assertEqual(form["task"], str(self.task.pk))
            self.assertTrue(form["csrfmiddlewaretoken"])
        missing_csrf = {key: value for key, value in forms[0].items() if key != "csrfmiddlewaretoken"}
        self.assertEqual(client.post(reverse("focus:home"), missing_csrf).status_code, 403)
        response = client.post(reverse("focus:home"), forms[0])
        session = FocusSession.objects.get(owner=self.user)
        self.assertEqual(session.task_id, self.task.pk)
        self.assertRedirects(response, reverse("focus:session", args=[session.pk]))
        self.assertRedirects(client.post(reverse("focus:home"), forms[0]), reverse("focus:session", args=[session.pk]))
        self.assertEqual(FocusSession.objects.filter(owner=self.user).count(), 1)

    def test_warning_shortfall_matches_alerts_without_recalculating_conflicts(self):
        self.session(self.now + timedelta(hours=1), self.now + timedelta(hours=1, minutes=30), is_locked=True)
        dashboard = build_dashboard(self.user, now=self.now)
        alerts = build_alerts(self.user, now=self.now)
        self.assertEqual(dashboard["task_rows"][0]["missing"], alerts["task_alerts"][0]["missing"])
        self.assertEqual(dashboard["task_rows"][0]["missing"], 30)

    def test_session_groups_and_week_markers_use_only_owned_applied_data(self):
        self.session(self.now - timedelta(hours=2), self.now - timedelta(hours=1), status="done")
        self.session(self.now + timedelta(days=1), self.now + timedelta(days=1, hours=1))
        self.session(self.now + timedelta(hours=1), self.now + timedelta(hours=2), status="cancelled")
        draft = StudyPlan.objects.create(owner=self.user, week_start=self.plan.week_start)
        StudySession.objects.create(owner=self.user, plan=draft, task=self.task,
                                    starts_at=self.now, ends_at=self.now + timedelta(hours=1))
        Task.objects.create(owner=self.user, title="Việc đã xong", deadline=self.now + timedelta(days=2),
                            estimated_minutes=10, remaining_minutes=0, status="done")
        response = self.client.get(reverse("core:home"))
        groups = response.context["session_groups"]
        self.assertEqual([group["label"] for group in groups], ["Hôm nay", "Ngày mai"])
        self.assertIsNone(groups[0]["rows"][0]["action"])
        self.assertEqual(groups[1]["rows"][0]["action"]["method"], "post")
        days = response.context["week_days"]
        self.assertEqual(len(days), 7)
        self.assertEqual(sum(day["today"] for day in days), 1)
        self.assertEqual(sum(day["sessions"] for day in days), 2)
        self.assertEqual(sum(day["deadlines"] for day in days), 2)
        self.assertContains(response, "Đã ghi nhận")
        self.assertNotContains(response, 'class="metric-overdue"')

    def test_old_unrecorded_session_wins_even_outside_current_week(self):
        past = self.session(self.now - timedelta(days=20, hours=1), self.now - timedelta(days=20))
        context = build_dashboard(self.user, now=self.now)
        self.assertEqual(context["action"]["kind"], "unrecorded")
        self.assertEqual(context["action"]["primary"]["pk"], past.pk)

    def test_complete_dashboard_stays_within_twelve_queries(self):
        for user in (self.new_user, self.user):
            self.client.force_login(user)
            with self.assertNumQueries(12):
                self.assertEqual(self.client.get(reverse("core:home")).status_code, 200)
        FocusSession.objects.create(owner=self.user, task=self.task, task_title=self.task.title, resumed_at=self.now)
        with self.assertNumQueries(12):
            self.assertEqual(self.client.get(reverse("core:home")).status_code, 200)
