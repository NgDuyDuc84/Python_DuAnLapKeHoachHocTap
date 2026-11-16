import io
import smtplib
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.management import call_command, CommandError
from django.db import IntegrityError, OperationalError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from planner.models import StudyPlan, StudySession
from studies.models import Task

from .forms import ReminderPreferenceForm
from .models import Reminder, ReminderPreference
from .services import dispatch_one, enqueue_due_reminders, get_preferences, recover_stale_claims, run_cycle

NOW = timezone.make_aware(datetime(2026, 11, 13, 9))


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", SITE_URL="https://study.example.test")
class ReminderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="reminder_a", email="a@example.test")
        cls.other = get_user_model().objects.create_user(username="reminder_b", email="b@example.test")
        cls.task = Task.objects.create(owner=cls.owner, title="Sắp nộp Python", deadline=NOW + timedelta(minutes=30), estimated_minutes=60, remaining_minutes=60)
        cls.later_task = Task.objects.create(owner=cls.owner, title="Ôn lý thuyết", deadline=NOW + timedelta(days=3), estimated_minutes=60, remaining_minutes=60)
        cls.plan = StudyPlan.objects.create(owner=cls.owner, week_start=NOW.date() - timedelta(days=NOW.weekday()), applied_at=NOW)
        cls.session = StudySession.objects.create(owner=cls.owner, task=cls.later_task, plan=cls.plan, starts_at=NOW + timedelta(minutes=10), ends_at=NOW + timedelta(minutes=40))
        cls.preferences = ReminderPreference.objects.create(owner=cls.owner, in_app_enabled=True, email_enabled=True, deadline_minutes=60, session_minutes=15)

    def setUp(self):
        self.clock = patch("notifications.services.timezone.now", return_value=NOW)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.client.force_login(self.owner)

    def preference(self, **values):
        ReminderPreference.objects.filter(owner=self.owner).update(**values)

    def queued(self, channel=Reminder.Channel.EMAIL, kind=Reminder.Kind.DEADLINE):
        enqueue_due_reminders(now=NOW)
        return Reminder.objects.get(owner=self.owner, channel=channel, kind=kind)

    def test_unsaved_defaults_enable_web_only_and_get_does_not_write_preferences(self):
        self.preferences.delete()
        self.assertIsNone(get_preferences(self.owner).pk)
        run_cycle(now=NOW)
        self.assertEqual(Reminder.objects.filter(channel="in_app", status="sent").count(), 2)
        self.assertFalse(Reminder.objects.filter(channel="email").exists())
        self.assertFalse(ReminderPreference.objects.filter(owner=self.owner).exists())

    def test_queue_is_not_visible_or_sent_before_worker_dispatch(self):
        self.assertEqual(enqueue_due_reminders(now=NOW), 4)
        self.assertEqual(Reminder.objects.filter(status="pending").count(), 4)
        self.assertNotContains(self.client.get(reverse("notifications:inbox")), self.task.title)
        self.assertEqual(len(mail.outbox), 0)

    def test_repeated_cycles_deliver_once_per_event_and_channel(self):
        self.assertEqual(run_cycle(now=NOW), {"created": 4, "delivered": 4})
        self.assertEqual(run_cycle(now=NOW), {"created": 0, "delivered": 0})
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(Reminder.objects.filter(channel="in_app", status="sent").count(), 2)
        self.assertEqual(list(Reminder.objects.filter(channel="email").values_list("attempts", flat=True)), [1, 1])

    def test_due_boundaries_exclude_past_and_include_exact_lead_time(self):
        tasks = []
        for minutes in (0, 60, 61):
            tasks.append(Task.objects.create(owner=self.owner, title=f"Boundary {minutes}", deadline=NOW + timedelta(minutes=minutes), estimated_minutes=1, remaining_minutes=1))
        enqueue_due_reminders(now=NOW)
        included = set(Reminder.objects.filter(task__in=tasks).values_list("task_id", flat=True))
        self.assertEqual(included, {tasks[1].pk})

    def test_only_unfinished_tasks_and_applied_planned_future_sessions_are_queued(self):
        Task.objects.filter(pk=self.task.pk).update(status="done", remaining_minutes=0)
        StudySession.objects.filter(pk=self.session.pk).update(status="cancelled")
        draft = StudyPlan.objects.create(owner=self.owner, week_start=self.plan.week_start)
        StudySession.objects.create(owner=self.owner, task=self.later_task, plan=draft, starts_at=NOW + timedelta(minutes=5), ends_at=NOW + timedelta(minutes=30))
        self.assertEqual(enqueue_due_reminders(now=NOW), 0)
        self.session.status = "done"
        self.session.save()
        self.assertEqual(enqueue_due_reminders(now=NOW), 0)

    def test_both_channels_off_and_inactive_users_do_not_create_new_reminders(self):
        self.preference(in_app_enabled=False, email_enabled=False)
        self.assertEqual(run_cycle(now=NOW)["created"], 0)
        self.preference(in_app_enabled=True, email_enabled=True)
        get_user_model().objects.filter(pk=self.owner.pk).update(is_active=False)
        self.assertEqual(run_cycle(now=NOW)["created"], 0)

    def test_completion_before_send_skips_stale_reminder(self):
        reminder = self.queued()
        Task.objects.filter(pk=self.task.pk).update(status="done", remaining_minutes=0)
        self.assertFalse(dispatch_one(reminder.pk, now=NOW))
        reminder.refresh_from_db()
        self.assertEqual(reminder.status, "skipped")
        self.assertEqual(len(mail.outbox), 0)

    def test_changed_deadline_is_skipped_and_new_time_gets_new_event(self):
        old = self.queued()
        Task.objects.filter(pk=self.task.pk).update(deadline=NOW + timedelta(minutes=45))
        self.assertFalse(dispatch_one(old.pk, now=NOW))
        enqueue_due_reminders(now=NOW)
        self.assertEqual(Reminder.objects.filter(task=self.task, channel="email").count(), 2)
        new = Reminder.objects.filter(task=self.task, channel="email").exclude(pk=old.pk).get()
        self.assertTrue(dispatch_one(new.pk, now=NOW))
        self.assertEqual(len(mail.outbox), 1)

    def test_moved_cancelled_or_deleted_session_is_not_sent(self):
        for action in ("move", "cancel", "delete"):
            session = StudySession.objects.create(owner=self.owner, task=self.later_task, plan=self.plan, starts_at=NOW + timedelta(minutes=12), ends_at=NOW + timedelta(minutes=35))
            enqueue_due_reminders(now=NOW)
            reminder = Reminder.objects.get(study_session=session, channel="email")
            if action == "move":
                StudySession.objects.filter(pk=session.pk).update(starts_at=NOW + timedelta(minutes=14))
            elif action == "cancel":
                StudySession.objects.filter(pk=session.pk).update(status="cancelled")
            else:
                session.delete()
            self.assertFalse(dispatch_one(reminder.pk, now=NOW))
            reminder.refresh_from_db()
            self.assertEqual(reminder.status, "skipped")
        self.assertEqual(len(mail.outbox), 0)

    def test_deleted_task_preserves_history_but_never_sends_pending_email(self):
        reminder = self.queued()
        title = reminder.title
        self.task.delete()
        reminder.refresh_from_db()
        self.assertIsNone(reminder.task_id)
        self.assertEqual((reminder.title, reminder.target_url), (title, ""))
        self.assertFalse(dispatch_one(reminder.pk, now=NOW))

    def test_channel_off_or_account_locked_before_delivery_skips_email(self):
        reminder = self.queued()
        self.preference(email_enabled=False)
        dispatch_one(reminder.pk, now=NOW)
        reminder.refresh_from_db()
        self.assertEqual(reminder.status, "skipped")
        self.preference(email_enabled=True)
        enqueue_due_reminders(now=NOW)
        get_user_model().objects.filter(pk=self.owner.pk).update(is_active=False)
        self.assertFalse(dispatch_one(reminder.pk, now=NOW))
        self.assertEqual(len(mail.outbox), 0)

    def test_newly_enabled_email_does_not_duplicate_web_notification(self):
        self.preference(email_enabled=False)
        run_cycle(now=NOW)
        self.preference(email_enabled=True)
        run_cycle(now=NOW)
        self.assertEqual(Reminder.objects.filter(channel="in_app").count(), 2)
        self.assertEqual(len(mail.outbox), 2)

    def test_skipped_due_to_disabled_channel_reactivates_while_still_eligible(self):
        reminder = self.queued()
        self.preference(email_enabled=False)
        dispatch_one(reminder.pk, now=NOW)
        self.preference(email_enabled=True)
        enqueue_due_reminders(now=NOW)
        self.assertTrue(dispatch_one(reminder.pk, now=NOW))
        self.assertEqual(len(mail.outbox), 1)

    def test_changing_lead_does_not_resend_an_already_sent_event(self):
        run_cycle(now=NOW)
        self.preference(deadline_minutes=180, session_minutes=30)
        self.assertEqual(run_cycle(now=NOW), {"created": 0, "delivered": 0})
        self.assertEqual(len(mail.outbox), 2)

    def test_reducing_lead_defers_pending_event_until_new_due_time(self):
        self.preference(deadline_minutes=180)
        task = Task.objects.create(owner=self.owner, title="Later deadline", deadline=NOW + timedelta(minutes=120), estimated_minutes=10, remaining_minutes=10)
        enqueue_due_reminders(now=NOW)
        reminder = Reminder.objects.get(task=task, channel="email")
        self.preference(deadline_minutes=60)
        self.assertFalse(dispatch_one(reminder.pk, now=NOW))
        reminder.refresh_from_db()
        self.assertEqual((reminder.status, reminder.next_attempt_at), ("pending", NOW + timedelta(minutes=60)))
        self.assertTrue(dispatch_one(reminder.pk, now=NOW + timedelta(minutes=60)))

    def test_worker_catches_up_only_before_target_and_uses_live_title(self):
        reminder = self.queued()
        Task.objects.filter(pk=self.task.pk).update(title="Tên mới\nkhông tạo header")
        self.assertTrue(dispatch_one(reminder.pk, now=NOW + timedelta(minutes=29)))
        self.assertIn("Tên mới", mail.outbox[0].subject)
        self.assertNotIn("\n", mail.outbox[0].subject)
        self.assertIn("https://study.example.test/studies/tasks/", mail.outbox[0].body)
        self.assertIn("https://study.example.test/notifications/preferences/", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, ["a@example.test"])
        reminder.refresh_from_db()
        self.assertIn("a@example.test", reminder.message)
        with override_settings(EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"):
            self.assertContains(self.client.get(reverse("notifications:email_history")), "Chế độ tại lần thử: kiểm thử")
        session_reminder = Reminder.objects.get(study_session=self.session, channel="email")
        self.assertFalse(dispatch_one(session_reminder.pk, now=NOW + timedelta(minutes=10)))

    def test_rejected_email_retries_three_times_one_minute_apart(self):
        reminder = self.queued()
        with patch("notifications.services.send_mail", side_effect=smtplib.SMTPDataError(550, b"rejected")) as sender:
            for minute in range(3):
                self.assertFalse(dispatch_one(reminder.pk, now=NOW + timedelta(minutes=minute)))
            self.assertFalse(dispatch_one(reminder.pk, now=NOW + timedelta(minutes=3)))
            self.assertEqual(sender.call_count, 3)
        reminder.refresh_from_db()
        self.assertEqual((reminder.status, reminder.attempts), ("failed", 3))
        self.assertNotIn("rejected", reminder.last_error)

    def test_retry_not_due_does_not_send_then_success_keeps_attempt_count(self):
        reminder = self.queued()
        with patch("notifications.services.send_mail", return_value=0):
            dispatch_one(reminder.pk, now=NOW)
        self.assertFalse(dispatch_one(reminder.pk, now=NOW + timedelta(seconds=59)))
        self.assertTrue(dispatch_one(reminder.pk, now=NOW + timedelta(minutes=1)))
        reminder.refresh_from_db()
        self.assertEqual((reminder.status, reminder.attempts), ("sent", 2))
        self.assertEqual(len(mail.outbox), 1)

    def test_disconnect_is_uncertain_and_not_automatically_retried(self):
        reminder = self.queued()
        with patch("notifications.services.send_mail", side_effect=smtplib.SMTPServerDisconnected("private server detail")):
            self.assertFalse(dispatch_one(reminder.pk, now=NOW))
        self.assertFalse(dispatch_one(reminder.pk, now=NOW + timedelta(minutes=2)))
        reminder.refresh_from_db()
        self.assertEqual((reminder.status, reminder.attempts), ("uncertain", 1))
        self.assertNotIn("private server", reminder.last_error)

    def test_invalid_email_fails_without_calling_sender(self):
        reminder = self.queued()
        get_user_model().objects.filter(pk=self.owner.pk).update(email="")
        with patch("notifications.services.send_mail") as sender:
            dispatch_one(reminder.pk, now=NOW)
            sender.assert_not_called()
        reminder.refresh_from_db()
        self.assertEqual(reminder.status, "failed")

    def test_live_claim_cannot_be_claimed_twice_and_stale_claim_recovery(self):
        reminder = self.queued()
        web = Reminder.objects.get(task=self.task, channel="in_app")
        for row in (reminder, web):
            Reminder.objects.filter(pk=row.pk).update(status="sending", claim_token=uuid.uuid4(), claimed_at=NOW)
            self.assertFalse(dispatch_one(row.pk, now=NOW))
        recover_stale_claims(now=NOW + timedelta(minutes=4))
        reminder.refresh_from_db()
        self.assertEqual(reminder.status, "sending")
        recover_stale_claims(now=NOW + timedelta(minutes=6))
        reminder.refresh_from_db()
        web.refresh_from_db()
        self.assertEqual((reminder.status, web.status), ("uncertain", "pending"))
        self.assertTrue(dispatch_one(web.pk, now=NOW + timedelta(minutes=6)))

    def test_lease_loss_during_send_does_not_overwrite_uncertain_result(self):
        reminder = self.queued()
        def interrupted(*args, **kwargs):
            recover_stale_claims(now=NOW + timedelta(minutes=6))
            return 1
        with patch("notifications.services.send_mail", side_effect=interrupted):
            self.assertFalse(dispatch_one(reminder.pk, now=NOW))
        reminder.refresh_from_db()
        self.assertEqual(reminder.status, "uncertain")

    def test_unique_constraint_and_model_ownership(self):
        reminder = self.queued()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Reminder.objects.create(owner=self.owner, task=self.task, kind="deadline", channel="email",
                dedup_key=reminder.dedup_key, target_at=self.task.deadline, remind_at=NOW, title="Duplicate", message="")
        reminder.full_clean()
        reminder.owner = self.other
        with self.assertRaises(ValidationError):
            reminder.full_clean()

    def test_preference_get_no_write_owner_spoof_choices_and_email_validation(self):
        self.preferences.delete()
        url = reverse("notifications:preferences")
        self.assertContains(self.client.get(url), "Tùy chọn nhắc việc")
        self.assertFalse(ReminderPreference.objects.filter(owner=self.owner).exists())
        data = {"owner": self.other.pk, "in_app_enabled": "on", "email_enabled": "on", "deadline_minutes": 60, "session_minutes": 5}
        self.assertEqual(self.client.post(url, data).status_code, 302)
        self.assertEqual(ReminderPreference.objects.get(owner=self.owner).session_minutes, 5)
        self.assertFalse(ReminderPreference.objects.filter(owner=self.other).exists())
        self.assertEqual(self.client.post(url, {**data, "session_minutes": 0}).status_code, 200)
        get_user_model().objects.filter(pk=self.owner.pk).update(email="")
        self.owner.refresh_from_db()
        self.assertFalse(ReminderPreferenceForm(data, instance=get_preferences(self.owner), user=self.owner).is_valid())

    def test_inbox_read_filter_and_read_all_only_affect_current_owner(self):
        run_cycle(now=NOW)
        web = Reminder.objects.filter(owner=self.owner, channel="in_app").first()
        other_task = Task.objects.create(owner=self.other, title="Private B", deadline=NOW + timedelta(minutes=20), estimated_minutes=1, remaining_minutes=1)
        run_cycle(now=NOW)
        other_web = Reminder.objects.get(owner=self.other, channel="in_app")
        inbox = reverse("notifications:inbox")
        self.assertEqual(self.client.get(inbox).context["unread_count"], 2)
        self.assertNotContains(self.client.get(inbox), other_task.title)
        self.assertEqual(self.client.post(reverse("notifications:read", args=[web.pk])).status_code, 302)
        self.assertEqual(self.client.get(inbox, {"state": "unread"}).context["unread_count"], 1)
        self.client.post(reverse("notifications:read_all"))
        self.assertEqual(self.client.get(inbox, {"state": "unread"}).context["paginator"].count, 0)
        other_web.refresh_from_db()
        self.assertIsNone(other_web.read_at)

    def test_inbox_get_does_not_mark_read_or_run_worker_and_bad_filter_has_errors(self):
        run_cycle(now=NOW)
        count = Reminder.objects.count()
        response = self.client.get(reverse("notifications:inbox"))
        self.assertEqual(Reminder.objects.count(), count)
        self.assertFalse(Reminder.objects.filter(read_at__isnull=False).exists())
        self.assertEqual(response.status_code, 200)
        invalid = self.client.get(reverse("notifications:inbox"), {"state": "bad"})
        self.assertTrue(invalid.context["filter_form"].errors)

    def test_manual_retry_queues_only_failed_or_uncertain_without_sending_in_request(self):
        reminder = self.queued()
        Reminder.objects.filter(pk=reminder.pk).update(status="uncertain", attempts=3)
        url = reverse("notifications:retry_email", args=[reminder.pk])
        self.assertEqual(self.client.post(url).status_code, 302)
        reminder.refresh_from_db()
        self.assertEqual((reminder.status, reminder.attempts), ("pending", 0))
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertTrue(dispatch_one(reminder.pk, now=NOW))
        self.client.post(url)
        reminder.refresh_from_db()
        self.assertEqual((reminder.status, reminder.attempts), ("sent", 1))

    def test_private_routes_post_only_and_csrf(self):
        reminder = self.queued()
        web = Reminder.objects.get(task=self.task, channel="in_app")
        urls = [reverse("notifications:read", args=[web.pk]), reverse("notifications:retry_email", args=[reminder.pk]), reverse("notifications:read_all")]
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 405)
        secure = Client(enforce_csrf_checks=True)
        secure.force_login(self.owner)
        for url in urls + [reverse("notifications:preferences")]:
            self.assertEqual(secure.post(url).status_code, 403)
        self.client.force_login(self.other)
        for url in urls[:2]:
            self.assertEqual(self.client.post(url).status_code, 404)
        self.client.logout()
        for name in ("inbox", "email_history", "preferences"):
            self.assertEqual(self.client.get(reverse(f"notifications:{name}")).status_code, 302)

    def test_email_history_is_private_and_renders_retry_and_test_mode(self):
        reminder = self.queued()
        Reminder.objects.filter(pk=reminder.pk).update(status="uncertain", last_error="Kiểm tra hộp thư")
        history = reverse("notifications:email_history")
        self.assertContains(self.client.get(history), "Đã kiểm tra hộp thư, yêu cầu gửi lại")
        self.assertContains(self.client.get(history), "Gửi email nhắc việc hiện chưa khả dụng.")
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(history), self.task.title)

    # TestCase owns its transaction; real connection cleanup is covered by WorkerConnectionTests.
    @patch("notifications.management.commands.process_reminders.close_old_connections")
    def test_command_once_is_idempotent_and_watch_can_stop_without_traceback(self, _close_connections):
        output = io.StringIO()
        call_command("process_reminders", stdout=output)
        self.assertIn("Đã tạo 4 nhắc", output.getvalue())
        call_command("process_reminders", stdout=output)
        self.assertIn("Đã tạo 0 nhắc", output.getvalue())
        with patch("notifications.management.commands.process_reminders.time.sleep", side_effect=KeyboardInterrupt):
            call_command("process_reminders", watch=True, interval=1, stdout=output)
        self.assertIn("Đã dừng worker", output.getvalue())
        with self.assertRaises(CommandError):
            call_command("process_reminders", interval=0, stdout=output)

    @patch("notifications.management.commands.process_reminders.close_old_connections")
    def test_watch_continues_after_database_busy_and_one_shot_reports_failure(self, _close_connections):
        output, errors = io.StringIO(), io.StringIO()
        command = "notifications.management.commands.process_reminders"
        with patch(f"{command}.run_cycle", side_effect=[OperationalError("database is locked"), {"created": 0, "delivered": 0}]), patch(f"{command}.time.sleep", side_effect=[None, KeyboardInterrupt]):
            call_command("process_reminders", watch=True, interval=1, stdout=output, stderr=errors)
        self.assertIn("worker sẽ thử lại", errors.getvalue())
        self.assertIn("Đã tạo 0 nhắc", output.getvalue())
        with patch(f"{command}.run_cycle", side_effect=OperationalError("database is locked")), self.assertRaises(CommandError):
            call_command("process_reminders", stdout=output)
