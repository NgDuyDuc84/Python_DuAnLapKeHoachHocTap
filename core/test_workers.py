from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from integrations.models import CalendarConnection, CalendarSyncJob
from integrations.services import queue_job, snapshot
from notifications.models import Reminder, ReminderPreference
from studies.models import Task


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class WorkerConnectionTests(TransactionTestCase):
    """Workers manage their own connections, outside TestCase's atomic wrapper."""

    def setUp(self):
        self.user = get_user_model().objects.create_user("worker-connection-test")

    def test_reminder_worker_reconnects_and_preserves_saved_data(self):
        Task.objects.create(
            owner=self.user, title="Synthetic reminder", deadline=timezone.now() + timedelta(hours=1),
            estimated_minutes=20, remaining_minutes=20,
        )
        ReminderPreference.objects.create(owner=self.user, email_enabled=False)
        old_connection = connection.connection
        connection.close_at = 0  # The next worker cycle must clean up an expired connection.
        with patch("requests.sessions.Session.request") as external:
            call_command("process_reminders", stdout=StringIO())
        external.assert_not_called()
        self.assertEqual(Reminder.objects.filter(owner=self.user, status="sent", channel="in_app").count(), 1)
        call_command("process_reminders", stdout=StringIO())
        self.assertEqual(Reminder.objects.filter(owner=self.user).count(), 1)
        if connection.vendor == "postgresql":
            self.assertTrue(old_connection.closed)

    def test_calendar_worker_reconnects_and_finishes_an_empty_week(self):
        calendar = CalendarConnection.objects.create(owner=self.user, is_connected=True)
        today = timezone.localdate()
        week = today - timedelta(days=today.weekday())
        job, created = queue_job(calendar, week, snapshot(calendar, week)["hash"])
        self.assertTrue(created)
        old_connection = connection.connection
        connection.close_at = 0
        with patch("requests.sessions.Session.request") as external:
            call_command("process_calendar_sync", stdout=StringIO())
        external.assert_not_called()
        job.refresh_from_db()
        self.assertEqual(job.status, CalendarSyncJob.Status.SUCCESS)
        self.assertEqual(job.results, {"updated": 0, "deleted": 0})
        if connection.vendor == "postgresql":
            self.assertTrue(old_connection.closed)
