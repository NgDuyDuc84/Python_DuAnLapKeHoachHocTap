import copy
import time
import uuid
from datetime import datetime, time as day_time, timedelta
from io import BytesIO, StringIO, TextIOWrapper
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import requests
from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from google.oauth2.credentials import Credentials

from planner.models import StudyPlan, StudySession
from studies.models import Subject, Task

from .google import (
    CALENDAR_SCOPE, SCOPES, GoogleCalendarClient, SyncError, configured,
    decrypt_credentials, encrypt_credentials, google_identity,
)
from .models import CalendarConnection, CalendarEventMapping, CalendarSyncJob
from .services import queue_job, run_cycle, run_job, snapshot


def credentials():
    return Credentials(
        "synthetic-access", refresh_token="synthetic-refresh",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="synthetic-client", client_secret="synthetic-secret",
        scopes=SCOPES, granted_scopes=SCOPES,
    )


class FakeGoogle:
    def __init__(self, connection):
        self.events = {}
        self.calendars = 0
        self.writes = []

    def create_calendar(self):
        self.calendars += 1
        return {"id": "synthetic-calendar"}

    def calendar(self, calendar_id):
        return {"id": calendar_id}

    def event(self, calendar_id, event_id):
        return copy.deepcopy(self.events.get(event_id))

    def upsert(self, calendar_id, event_id, payload, *, exists):
        self.writes.append(("patch" if exists else "insert", event_id))
        self.events[event_id] = {"id": event_id, **copy.deepcopy(payload)}
        return copy.deepcopy(self.events[event_id])

    def delete(self, calendar_id, event_id):
        self.writes.append(("delete", event_id))
        self.events.pop(event_id, None)

    def close(self):
        pass


@override_settings(
    GOOGLE_CLIENT_ID="synthetic-client", GOOGLE_CLIENT_SECRET="synthetic-secret",
    GOOGLE_TOKEN_ENCRYPTION_KEY=Fernet.generate_key().decode(),
    GOOGLE_REDIRECT_URI="http://127.0.0.1:8000/integrations/google/callback/",
)
class CalendarTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("calendar-a", password="Test-synthetic-93")
        self.other = get_user_model().objects.create_user("calendar-b", password="Test-synthetic-94")
        self.client.force_login(self.user)
        today = timezone.localdate() + timedelta(days=8)
        self.week = today - timedelta(days=today.weekday())
        self.subject = Subject.objects.create(owner=self.user, name="Python")
        self.task = Task.objects.create(
            owner=self.user, subject=self.subject, title="Làm bài Python",
            deadline=timezone.make_aware(datetime.combine(self.week + timedelta(days=6), day_time(22))),
            estimated_minutes=100, remaining_minutes=100,
        )
        self.plan = StudyPlan.objects.create(owner=self.user, week_start=self.week, applied_at=timezone.now())
        self.session = StudySession.objects.create(
            owner=self.user, plan=self.plan, task=self.task,
            starts_at=timezone.make_aware(datetime.combine(self.week, day_time(9))),
            ends_at=timezone.make_aware(datetime.combine(self.week, day_time(9, 50))),
        )
        self.connection = CalendarConnection.objects.create(
            owner=self.user, google_sub="synthetic-sub", email="calendar@example.test",
            encrypted_credentials=encrypt_credentials(credentials()), is_connected=True,
        )
        self.google = FakeGoogle(self.connection)

    def new_job(self):
        self.connection.refresh_from_db()
        data = snapshot(self.connection, self.week)
        job, created = queue_job(self.connection, self.week, data["hash"])
        self.assertTrue(created)
        return job

    def execute(self, job=None):
        job = job or self.new_job()
        self.assertTrue(run_job(job.pk, client_class=lambda connection: self.google))
        job.refresh_from_db()
        return job

    def preview(self):
        return self.client.get(reverse("integrations:google"), {"week": self.week.isoformat()})

    def pending_oauth(self, **overrides):
        value = {"state": "synthetic-state", "verifier": "synthetic-pkce", "issued": time.time(), "owner": self.user.pk}
        value.update(overrides)
        session = self.client.session
        session["google_oauth"] = value
        session.save()

    def callback(self, **query):
        return self.client.get(reverse("integrations:callback"), {"state": "synthetic-state", "code": "synthetic-code", **query})

    def test_login_required_and_post_only(self):
        self.client.logout()
        self.assertRedirects(self.client.get(reverse("integrations:google")), "/accounts/login/?next=/integrations/google/", fetch_redirect_response=False)
        self.client.force_login(self.user)
        for name in ("connect", "sync", "disconnect", "reset"):
            self.assertEqual(self.client.get(reverse("integrations:" + name)).status_code, 405)

    def test_csrf_protects_external_mutations(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        for name in ("connect", "sync", "disconnect", "reset"):
            self.assertEqual(client.post(reverse("integrations:" + name)).status_code, 403)

    @override_settings(GOOGLE_CLIENT_ID="", GOOGLE_TOKEN_ENCRYPTION_KEY="")
    def test_unconfigured_does_not_break_web_or_start_oauth(self):
        self.assertFalse(configured())
        self.assertContains(self.client.get(reverse("integrations:google")), "Chưa cấu hình Google OAuth")
        self.assertRedirects(self.client.post(reverse("integrations:connect")), reverse("integrations:google"))

    def test_oauth_uses_offline_pkce_state_and_limited_scope(self):
        response = self.client.post(reverse("integrations:connect"))
        query = parse_qs(urlparse(response.url).query)
        pending = self.client.session["google_oauth"]
        self.assertEqual(query["state"], [pending["state"]])
        self.assertEqual(query["access_type"], ["offline"])
        self.assertEqual(query["code_challenge_method"], ["S256"])
        self.assertTrue(pending["verifier"])
        self.assertIn(CALENDAR_SCOPE, query["scope"][0])
        self.assertNotIn("https://www.googleapis.com/auth/calendar.events ", query["scope"][0])
        self.assertEqual(query["redirect_uri"], ["http://127.0.0.1:8000/integrations/google/callback/"])

    @patch("integrations.views.oauth_flow")
    def test_invalid_expired_wrong_owner_and_replayed_states_never_exchange_code(self, flow):
        for overrides in ({"state": "wrong"}, {"issued": time.time() - 601}, {"owner": self.other.pk}):
            self.pending_oauth(**overrides)
            self.callback()
            self.assertNotIn("google_oauth", self.client.session)
        self.pending_oauth()
        self.callback(state="không hợp lệ")
        self.callback()
        flow.assert_not_called()

    @patch("integrations.views.oauth_flow")
    def test_denied_consent_does_not_exchange_code(self, flow):
        self.pending_oauth()
        self.callback(error="access_denied")
        flow.assert_not_called()

    @patch("integrations.views.google_identity", return_value={"sub": "synthetic-sub", "email": "new@example.test"})
    @patch("integrations.views.oauth_flow")
    def test_callback_encrypts_tokens_and_keeps_calendar_on_same_account(self, flow, identity):
        self.connection.calendar_id = "existing-calendar"
        self.connection.calendar_state = "ready"
        self.connection.save()
        old_generation = self.connection.generation
        flow.return_value.credentials = credentials()
        self.pending_oauth()
        response = self.callback()
        self.assertEqual(response.status_code, 302)
        flow.return_value.fetch_token.assert_called_once_with(code="synthetic-code", timeout=15)
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.calendar_id, "existing-calendar")
        self.assertNotEqual(self.connection.generation, old_generation)
        self.assertNotIn("synthetic-refresh", self.connection.encrypted_credentials)
        self.assertEqual(decrypt_credentials(self.connection.encrypted_credentials).refresh_token, "synthetic-refresh")
        self.assertNotIn("synthetic-refresh", str(self.client.session.items()))
        self.assertNotContains(self.client.get(response.url), "synthetic-access")

    @patch("integrations.views.google_identity", return_value={"sub": "other-sub", "email": "other@example.test"})
    @patch("integrations.views.oauth_flow")
    def test_cannot_silently_switch_connected_google_account(self, flow, identity):
        flow.return_value.credentials = credentials()
        self.pending_oauth()
        self.callback()
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.google_sub, "synthetic-sub")

    @patch("integrations.views.revoke_credentials", return_value=False)
    def test_disconnect_clears_tokens_invalidates_jobs_and_explains_revoke_failure(self, revoke):
        job = self.new_job()
        self.pending_oauth()
        response = self.client.post(reverse("integrations:disconnect"), follow=True)
        self.connection.refresh_from_db()
        job.refresh_from_db()
        self.assertFalse(self.connection.is_connected)
        self.assertEqual(self.connection.encrypted_credentials, "")
        self.assertNotIn("google_oauth", self.client.session)
        self.assertEqual(job.status, "stale")
        self.assertFalse(run_job(job.pk, client_class=lambda connection: self.google))
        self.assertContains(response, "Chưa xác nhận thu hồi quyền")

    def test_preview_is_read_only_and_hides_other_users(self):
        StudySession.objects.create(owner=self.other, plan=StudyPlan.objects.create(
            owner=self.other, week_start=self.week, applied_at=timezone.now(),
        ), task=Task.objects.create(owner=self.other, title="PRIVATE-OTHER", deadline=self.task.deadline, estimated_minutes=50, remaining_minutes=50), starts_at=self.session.starts_at, ends_at=self.session.ends_at)
        response = self.preview()
        self.assertContains(response, "Làm bài Python")
        self.assertNotContains(response, "PRIVATE-OTHER")
        self.assertEqual(CalendarSyncJob.objects.count(), 0)
        self.assertEqual(CalendarEventMapping.objects.count(), 0)

    def test_draft_and_cancelled_excluded_done_included(self):
        self.session.status = "cancelled"
        self.session.save()
        self.assertEqual(snapshot(self.connection, self.week)["desired"], {})
        self.session.status = "done"
        self.session.save()
        self.assertIn("Đã học", snapshot(self.connection, self.week)["desired"][self.session.pk]["summary"])
        self.plan.applied_at = None
        self.plan.save()
        self.assertEqual(snapshot(self.connection, self.week)["desired"], {})

    def test_preview_queue_and_duplicate_submission(self):
        token = self.preview().context["token"]
        response = self.client.post(reverse("integrations:sync"), {"preview": token})
        self.assertEqual(CalendarSyncJob.objects.count(), 1)
        self.assertEqual(CalendarSyncJob.objects.get().status, "pending")
        self.client.post(reverse("integrations:sync"), {"preview": token})
        self.assertEqual(CalendarSyncJob.objects.count(), 1)
        self.assertRedirects(response, reverse("integrations:job", args=[CalendarSyncJob.objects.get().pk]))

    def test_tampered_expired_stale_or_other_owner_preview_cannot_queue(self):
        token = self.preview().context["token"]
        self.client.post(reverse("integrations:sync"), {"preview": token + "tampered"})
        self.task.title = "Đã sửa sau xem trước"
        self.task.save()
        self.client.post(reverse("integrations:sync"), {"preview": token})
        with patch("django.core.signing.time.time", return_value=time.time() - 601):
            token = self.preview().context["token"]
        self.client.post(reverse("integrations:sync"), {"preview": token})
        token = self.preview().context["token"]
        self.client.force_login(self.other)
        CalendarConnection.objects.create(owner=self.other, is_connected=True)
        self.client.post(reverse("integrations:sync"), {"preview": token})
        self.assertEqual(CalendarSyncJob.objects.count(), 0)

    def test_job_detail_is_private(self):
        job = self.new_job()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("integrations:job", args=[job.pk])).status_code, 404)

    def test_create_repeat_update_use_same_event_and_calendar(self):
        first = self.execute()
        self.assertEqual(first.status, "success")
        self.assertEqual(first.results, {"updated": 1, "deleted": 0})
        mapping = CalendarEventMapping.objects.get()
        self.assertRegex(mapping.event_id, "^[0-9a-v]{5,}$")
        self.task.title = "Tên mới"
        self.task.save()
        self.session.starts_at += timedelta(hours=1)
        self.session.ends_at += timedelta(hours=1)
        self.session.save()
        second = self.execute()
        self.assertEqual(second.status, "success")
        self.assertEqual(self.google.calendars, 1)
        self.assertEqual(len(self.google.events), 1)
        self.assertEqual(self.google.events[mapping.event_id]["summary"], "Tên mới")
        self.assertEqual(self.google.writes[-1], ("patch", mapping.event_id))

    def test_direct_google_edits_are_overwritten(self):
        self.execute()
        mapping = CalendarEventMapping.objects.get()
        self.google.events[mapping.event_id]["summary"] = "Google edit"
        self.execute()
        self.assertEqual(self.google.events[mapping.event_id]["summary"], self.task.title)

    def test_cancelled_session_is_deleted_without_invalidating_own_job(self):
        self.execute()
        self.session.status = "cancelled"
        self.session.save()
        job = self.execute()
        self.assertEqual(job.status, "success")
        self.assertEqual(job.results["deleted"], 1)
        self.assertEqual(self.google.events, {})
        self.assertTrue(CalendarEventMapping.objects.get().remote_deleted)

    def test_deleted_task_keeps_mapping_until_remote_cleanup(self):
        self.execute()
        self.task.delete()
        mapping = CalendarEventMapping.objects.get()
        self.assertIsNone(mapping.study_session_id)
        job = self.execute()
        self.assertEqual(job.status, "success")
        self.assertEqual(self.google.events, {})

    def test_deletions_restrict_to_selected_week(self):
        self.execute()
        self.session.delete()
        data = snapshot(self.connection, self.week + timedelta(days=7))
        self.assertEqual(data["deletions"], [])
        self.assertEqual(len(snapshot(self.connection, self.week)["deletions"]), 1)

    def test_missing_or_cancelled_remote_event_gets_new_id(self):
        self.execute()
        mapping = CalendarEventMapping.objects.get()
        old_id = mapping.event_id
        self.google.events[old_id] = {"id": old_id, "status": "cancelled"}
        self.execute()
        mapping.refresh_from_db()
        self.assertNotEqual(mapping.event_id, old_id)
        self.google.events.pop(mapping.event_id)
        old_id = mapping.event_id
        self.execute()
        mapping.refresh_from_db()
        self.assertNotEqual(mapping.event_id, old_id)

    def test_wrong_event_marker_blocks_update_and_delete(self):
        self.execute()
        mapping = CalendarEventMapping.objects.get()
        self.google.events[mapping.event_id]["extendedProperties"] = {}
        writes = len(self.google.writes)
        self.assertEqual(self.execute().error, "event_owner")
        self.session.status = "cancelled"
        self.session.save()
        self.assertEqual(self.execute().error, "event_owner")
        self.assertEqual(len(self.google.writes), writes)

    def test_event_response_lost_retries_existing_persisted_id(self):
        original = self.google.upsert

        def lost(*args, **kwargs):
            original(*args, **kwargs)
            raise SyncError("network")

        with patch.object(self.google, "upsert", side_effect=lost):
            self.assertEqual(self.execute().error, "network")
        mapping = CalendarEventMapping.objects.get()
        self.assertFalse(mapping.was_created)
        self.assertEqual(self.execute().status, "success")
        self.assertEqual(len(self.google.events), 1)
        self.assertEqual(CalendarEventMapping.objects.get().event_id, mapping.event_id)

    def test_insert_conflict_fetches_owned_event_and_patches(self):
        original = self.google.upsert
        calls = []

        def conflict(*args, **kwargs):
            calls.append(kwargs["exists"])
            result = original(*args, **kwargs)
            return result if kwargs["exists"] else {"conflict": True}

        with patch.object(self.google, "upsert", side_effect=conflict):
            self.assertEqual(self.execute().status, "success")
        self.assertEqual(calls, [False, True])
        self.assertEqual(len(self.google.events), 1)

    def test_calendar_creation_uncertainty_never_auto_creates_again(self):
        with patch.object(self.google, "create_calendar", side_effect=SyncError("network")) as create:
            self.assertEqual(self.execute().error, "calendar_uncertain")
            self.assertEqual(self.execute().error, "calendar_uncertain")
            create.assert_called_once()
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.calendar_state, "uncertain")
        self.client.post(reverse("integrations:reset"))
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.calendar_state, "uncertain")
        self.client.post(reverse("integrations:reset"), {"confirm": "checked"})
        self.assertEqual(self.execute().status, "success")

    def test_missing_calendar_does_not_silently_replace(self):
        self.execute()
        with patch.object(self.google, "calendar", return_value=None):
            self.assertEqual(self.execute().error, "calendar_missing")
        self.assertEqual(self.google.calendars, 1)

    @patch("integrations.views.revoke_credentials", return_value=True)
    def test_disconnect_during_calendar_creation_requires_check_before_recreation(self, revoke):
        self.connection.calendar_state = "creating"
        self.connection.save()
        self.client.post(reverse("integrations:disconnect"))
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.calendar_state, "uncertain")

    @patch("integrations.views.google_identity", return_value={"sub": "other-sub", "email": "other@example.test"})
    @patch("integrations.views.oauth_flow")
    def test_switching_disconnected_account_removes_old_mappings_and_target(self, flow, identity):
        self.execute()
        self.connection.refresh_from_db()
        self.connection.is_connected = False
        self.connection.save()
        flow.return_value.credentials = credentials()
        self.pending_oauth()
        self.callback()
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.google_sub, "other-sub")
        self.assertEqual(self.connection.calendar_id, "")
        self.assertEqual(CalendarEventMapping.objects.count(), 0)

    def test_reset_target_refuses_while_job_active_and_invalidates_old_preview(self):
        self.connection.last_error = "calendar_missing"
        self.connection.save()
        token = self.preview().context["token"]
        job = self.new_job()
        self.client.post(reverse("integrations:reset"), {"confirm": "checked"})
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.last_error, "calendar_missing")
        job.status = "failed"
        job.save()
        self.client.post(reverse("integrations:reset"), {"confirm": "checked"})
        self.client.post(reverse("integrations:sync"), {"preview": token})
        self.assertEqual(CalendarSyncJob.objects.count(), 1)

    def test_stale_creation_claim_is_not_repeated(self):
        self.connection.calendar_state = "creating"
        self.connection.save()
        self.assertEqual(self.execute().error, "calendar_uncertain")
        self.assertEqual(self.google.calendars, 0)

    def test_changed_input_or_connection_stops_queued_job(self):
        job = self.new_job()
        self.task.title = "Stale"
        self.task.save()
        self.assertEqual(self.execute(job).status, "stale")
        self.assertEqual(self.google.calendars, 0)
        job = self.new_job()
        CalendarConnection.objects.filter(pk=self.connection.pk).update(generation=uuid.uuid4())
        self.assertEqual(self.execute(job).status, "stale")

    def test_changed_data_during_network_stops_further_writes(self):
        original = self.google.calendar

        def change(calendar_id):
            self.task.title = "Changed during API"
            self.task.save()
            return original(calendar_id)

        with patch.object(self.google, "calendar", side_effect=change):
            self.assertEqual(self.execute().status, "stale")
        self.assertEqual(self.google.events, {})

    def test_fresh_claim_not_stolen_stale_claim_recovered(self):
        job = self.new_job()
        job.status = "running"
        job.started_at = timezone.now()
        job.claim_token = uuid.uuid4()
        job.save()
        self.assertFalse(run_job(job.pk, client_class=lambda connection: self.google))
        CalendarSyncJob.objects.filter(pk=job.pk).update(started_at=timezone.now() - timedelta(minutes=6))
        self.assertEqual(self.execute(job).status, "success")

    def test_old_worker_cannot_overwrite_disconnected_tokens_or_job(self):
        job = self.new_job()

        def disconnect(calendar_id):
            CalendarConnection.objects.filter(pk=self.connection.pk).update(is_connected=False, encrypted_credentials="", generation=uuid.uuid4())
            CalendarSyncJob.objects.filter(pk=job.pk).update(status="stale", claim_token=None)
            return {"id": calendar_id}

        with patch.object(self.google, "calendar", side_effect=disconnect):
            self.execute(job)
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.encrypted_credentials, "")
        job.refresh_from_db()
        self.assertEqual(job.status, "stale")

    # TestCase owns its transaction; real connection cleanup is covered by WorkerConnectionTests.
    @patch("integrations.management.commands.process_calendar_sync.close_old_connections")
    def test_worker_command_and_empty_queue(self, _close_connections):
        self.new_job()
        with patch("integrations.services.GoogleCalendarClient", return_value=self.google):
            output = StringIO()
            call_command("process_calendar_sync", stdout=output)
        self.assertIn("processed 1 sync job", output.getvalue())
        self.assertEqual(run_cycle(), 0)

    @patch("integrations.management.commands.process_calendar_sync.close_old_connections")
    def test_worker_output_supports_legacy_windows_terminal_encoding(self, _close_connections):
        output = TextIOWrapper(BytesIO(), encoding="cp1252")
        call_command("process_calendar_sync", stdout=output)
        output.flush()
        self.assertIn(b"processed 0", output.buffer.getvalue())

    def test_credentials_wrong_key_and_corrupted_value_are_safe_errors(self):
        for value in ("broken", self.connection.encrypted_credentials):
            with override_settings(GOOGLE_TOKEN_ENCRYPTION_KEY=Fernet.generate_key().decode()):
                with self.assertRaisesMessage(SyncError, "Không đọc được"):
                    decrypt_credentials(value)

    def test_google_identity_rejects_missing_grant_refresh_or_unverified_email(self):
        with patch("integrations.google.AuthorizedSession") as session:
            response = session.return_value.__enter__.return_value.get.return_value
            response.json.return_value = {"sub": "sub", "email": "test@example.test", "email_verified": True}
            self.assertEqual(google_identity(credentials())["sub"], "sub")
            limited = credentials()
            limited._granted_scopes = ["openid"]
            with self.assertRaises(SyncError):
                google_identity(limited)
            response.json.return_value["email_verified"] = False
            with self.assertRaises(SyncError):
                google_identity(credentials())

    def test_client_quotes_paths_uses_timeouts_and_safe_errors(self):
        with patch("integrations.google.AuthorizedSession") as session:
            response = session.return_value.request.return_value
            response.status_code = 200
            response.content = b"{}"
            response.json.return_value = {"id": "event"}
            client = GoogleCalendarClient(self.connection)
            client.event("email@calendar/unsafe", "event")
            args, kwargs = session.return_value.request.call_args
            self.assertEqual(args[1], "https://www.googleapis.com/calendar/v3/calendars/email%40calendar%2Funsafe/events/event")
            self.assertEqual(kwargs["timeout"], 15)
            response.status_code = 401
            with self.assertRaisesMessage(SyncError, "Quyền Google"):
                client.event("id", "event")
            response.status_code = 410
            self.assertIsNone(client.event("id", "event"))
            session.return_value.request.side_effect = requests.Timeout("SENSITIVE PROVIDER BODY")
            with self.assertRaises(SyncError) as error:
                client.event("id", "event")
            self.assertNotIn("SENSITIVE", str(error.exception))
