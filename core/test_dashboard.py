from datetime import datetime, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from focus.models import FocusSession, StudyLog
from notifications.models import Reminder
from planner.models import StudyPlan, StudySession
from studies.models import Task

from .dashboard import build_dashboard


class DashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("overview-a")
        cls.other = get_user_model().objects.create_user("overview-b")
        # 00:15 in Vietnam is still the preceding UTC date.
        cls.now = timezone.make_aware(datetime(2026, 11, 16, 0, 15))
        cls.today = timezone.localdate(cls.now)
        cls.task = Task.objects.create(
            owner=cls.user, title="Own upcoming task", deadline=cls.now + timedelta(days=5),
            estimated_minutes=60, remaining_minutes=60,
        )
        cls.plan = StudyPlan.objects.create(owner=cls.user, week_start=cls.today, applied_at=cls.now)

    def session(self, start, end, **kwargs):
        return StudySession.objects.create(
            owner=self.user, plan=self.plan, task=self.task, starts_at=start, ends_at=end, **kwargs,
        )

    def reminder(self, **kwargs):
        return Reminder.objects.create(**{
            "owner": self.user, "kind": Reminder.Kind.DEADLINE, "channel": Reminder.Channel.IN_APP,
            "dedup_key": str(Reminder.objects.count()), "target_at": self.now,
            "remind_at": self.now, "title": "Reminder", "message": "Message", "status": Reminder.Status.SENT,
            **kwargs,
        })

    def test_anonymous_landing_and_public_guide_have_working_navigation(self):
        response = self.client.get(reverse("core:home"))
        self.assertTemplateUsed(response, "core/home.html")
        self.assertNotContains(response, 'aria-label="Điều hướng chính"')
        response = self.client.get(reverse("core:guide"))
        self.assertContains(response, "Lập kế hoạch cùng Nhịp Học")
        self.assertContains(response, reverse("planner:preferences"))

    def test_empty_account_has_onboarding_and_zero_metrics(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse("core:home"))
        self.assertTemplateUsed(response, "core/dashboard.html")
        self.assertContains(response, "Chuẩn bị kế hoạch đầu tiên")
        self.assertEqual(response["Cache-Control"], "no-store")
        for key in ("today_count", "today_done", "weekly_minutes", "overdue_count"):
            self.assertEqual(response.context[key], 0)
        self.assertFalse(response.context["has_tasks"])
        self.assertNotContains(response, self.task.title)

    def test_today_counts_use_local_midnight_and_exclude_drafts_and_cancelled(self):
        midnight = self.now.replace(hour=0, minute=0)
        self.session(midnight, midnight + timedelta(minutes=30), status=StudySession.Status.DONE)
        self.session(midnight + timedelta(hours=8), midnight + timedelta(hours=9))
        self.session(midnight - timedelta(hours=1), midnight)
        self.session(midnight + timedelta(days=1), midnight + timedelta(days=1, hours=1))
        self.session(midnight + timedelta(hours=10), midnight + timedelta(hours=11), status=StudySession.Status.CANCELLED)
        draft = StudyPlan.objects.create(owner=self.user, week_start=self.today)
        StudySession.objects.create(owner=self.user, plan=draft, task=self.task,
                                    starts_at=midnight, ends_at=midnight + timedelta(minutes=50))
        context = build_dashboard(self.user, now=self.now)
        self.assertEqual(context["today_count"], 2)
        self.assertEqual(context["today_done"], 1)

    def test_minutes_cover_exactly_seven_local_dates_and_only_current_owner(self):
        for days, minutes, owner in [(0, 25, self.user), (6, 40, self.user), (7, 100, self.user), (-1, 80, self.user), (0, 90, self.other)]:
            StudyLog.objects.create(owner=owner, task_title="History", minutes=minutes,
                                    studied_on=self.today - timedelta(days=days))
        self.assertEqual(build_dashboard(self.user, now=self.now)["weekly_minutes"], 65)

    def test_urgent_tasks_include_overdue_and_sort_deadline_then_priority(self):
        overdue = Task.objects.create(owner=self.user, title="Overdue", deadline=self.now - timedelta(minutes=1),
                                      estimated_minutes=10, remaining_minutes=10)
        high = Task.objects.create(owner=self.user, title="High", deadline=self.task.deadline,
                                   priority=Task.Priority.HIGH, estimated_minutes=10, remaining_minutes=10)
        for owner, status, days in [(self.other, "todo", -1), (self.user, "done", -1), (self.user, "todo", 8)]:
            Task.objects.create(owner=owner, title="Excluded", deadline=self.now + timedelta(days=days),
                                estimated_minutes=10, remaining_minutes=0 if status == "done" else 10, status=status)
        context = build_dashboard(self.user, now=self.now)
        self.assertEqual(context["overdue_count"], 1)
        self.assertEqual(context["urgent_tasks"], [overdue, high, self.task])

    def test_upcoming_sessions_include_ongoing_but_not_finished_drafts_or_other_owner(self):
        ongoing = self.session(self.now - timedelta(minutes=10), self.now + timedelta(minutes=20))
        self.session(self.now - timedelta(hours=1), self.now)
        self.session(self.now + timedelta(hours=2), self.now + timedelta(hours=3), status="done")
        for hour in range(1, 8):
            self.session(self.now + timedelta(hours=hour), self.now + timedelta(hours=hour, minutes=30))
        other_plan = StudyPlan.objects.create(owner=self.other, week_start=self.today, applied_at=self.now)
        StudySession.objects.create(owner=self.other, plan=other_plan, task=self.task,
                                    starts_at=self.now, ends_at=self.now + timedelta(hours=1))
        context = build_dashboard(self.user, now=self.now)
        self.assertEqual(len(context["upcoming_sessions"]), 6)
        self.assertEqual(context["upcoming_sessions"][0], ongoing)
        self.assertTrue(all(s.owner_id == self.user.pk and s.status == "planned" for s in context["upcoming_sessions"]))

    def test_unread_count_excludes_pending_read_email_and_other_users(self):
        self.reminder()
        self.reminder(status=Reminder.Status.PENDING)
        self.reminder(read_at=self.now)
        self.reminder(channel=Reminder.Channel.EMAIL)
        self.reminder(owner=self.other)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("core:home")).context["header_unread_count"], 1)
        Reminder.objects.filter(owner=self.user).update(read_at=self.now)
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.context["header_unread_count"], 0)
        self.assertNotContains(response, "Thông báo chưa đọc")

    def test_active_focus_is_owned_and_user_text_is_escaped(self):
        active = FocusSession.objects.create(owner=self.user, task=self.task, task_title="<script>private</script>",
                                             status="paused", resumed_at=None)
        FocusSession.objects.create(owner=self.other, task_title="Other secret", resumed_at=self.now)
        self.client.force_login(self.user)
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, reverse("focus:session", args=[active.pk]))
        self.assertContains(response, "&lt;script&gt;private&lt;/script&gt;")
        self.assertNotContains(response, "Other secret")

    def test_dashboard_only_reads_and_never_calls_provider_or_creates_preferences(self):
        self.client.force_login(self.user)
        with patch("requests.sessions.Session.request") as provider, CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        provider.assert_not_called()
        for query in queries:
            self.assertTrue(query["sql"].lstrip().upper().startswith("SELECT"), query["sql"])
