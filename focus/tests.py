import uuid
from datetime import date, datetime, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, OperationalError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from studies.models import Subject, Task

from .forms import FocusStartForm, LogRangeForm, StudyLogForm
from .models import FocusSession, StudyLog
from .services import FocusError, add_manual_log, build_statistics, start_work, timer_action

NOW = timezone.make_aware(datetime(2026, 11, 13, 9))


class FocusTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="focus_a")
        cls.other = get_user_model().objects.create_user(username="focus_b")
        cls.subject = Subject.objects.create(owner=cls.owner, name="Python", semester="HK1")
        cls.task = Task.objects.create(owner=cls.owner, subject=cls.subject, title="Bài Python", deadline=NOW + timedelta(days=3), estimated_minutes=120, remaining_minutes=120)
        cls.foreign_task = Task.objects.create(owner=cls.other, title="Việc của B", deadline=NOW + timedelta(days=3), estimated_minutes=60, remaining_minutes=60)
        cls.done = Task.objects.create(owner=cls.owner, title="Đã xong", deadline=NOW, estimated_minutes=10, remaining_minutes=0, status=Task.Status.DONE)

    def setUp(self):
        self.clock = patch("focus.services.timezone.now", return_value=NOW)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.client.force_login(self.owner)

    def start(self, **kwargs):
        return start_work(self.owner, self.task.pk, uuid.uuid4(), **kwargs)

    def action(self, session, action, **kwargs):
        return timer_action(self.owner, session.pk, action, **kwargs)

    def log_data(self, **kwargs):
        return {"task": self.task, "studied_on": date(2026, 11, 13), "minutes": 30,
                "notes": "Ôn vòng lặp", "entry_key": uuid.uuid4(), **kwargs}

    def test_start_work_and_one_active_per_owner_including_paused(self):
        session = self.start()
        self.assertEqual((session.phase, session.status, session.duration_seconds), ("work", "running", 1500))
        with self.assertRaises(FocusError):
            self.start()
        self.action(session, "pause")
        with self.assertRaises(FocusError):
            self.start()
        other = start_work(self.other, self.foreign_task.pk, uuid.uuid4())
        self.assertNotEqual(other.pk, session.pk)

    def test_repeat_start_key_returns_original_even_after_finish(self):
        key = uuid.uuid4()
        session = start_work(self.owner, self.task.pk, key)
        self.assertEqual(start_work(self.owner, self.task.pk, key).pk, session.pk)
        self.action(session, "finish", now=NOW + timedelta(minutes=2))
        self.assertEqual(start_work(self.owner, self.task.pk, key).pk, session.pk)
        self.assertEqual(FocusSession.objects.filter(owner=self.owner).count(), 1)

    def test_done_and_foreign_task_rejected(self):
        with self.assertRaises(FocusError):
            start_work(self.owner, self.done.pk, uuid.uuid4())
        with self.assertRaises(Task.DoesNotExist):
            start_work(self.owner, self.foreign_task.pk, uuid.uuid4())

    def test_pause_resume_excludes_pause_and_is_idempotent(self):
        session = self.start()
        paused = self.action(session, "pause", now=NOW + timedelta(seconds=80))
        self.assertEqual(paused.elapsed(NOW + timedelta(hours=1)), 80)
        self.action(session, "pause", now=NOW + timedelta(minutes=10))
        self.action(session, "resume", now=NOW + timedelta(minutes=10))
        self.action(session, "resume", now=NOW + timedelta(minutes=11))
        finished = self.action(session, "finish", now=NOW + timedelta(minutes=12))
        self.assertEqual(finished.elapsed_seconds, 200)
        self.assertEqual(StudyLog.objects.get().minutes, 3)

    def test_elapsed_never_negative_and_caps_at_duration_after_long_absence(self):
        session = self.start()
        self.assertEqual(session.elapsed(NOW - timedelta(seconds=5)), 0)
        self.assertEqual(session.elapsed(NOW + timedelta(days=2)), 1500)
        self.action(session, "finish", now=NOW + timedelta(days=2))
        log = StudyLog.objects.get()
        self.assertEqual((log.minutes, log.studied_on), (25, NOW.date()))

    def test_expired_paused_session_must_finish_instead_of_resume(self):
        session = self.start()
        self.action(session, "pause", now=NOW + timedelta(minutes=30))
        with self.assertRaises(FocusError):
            self.action(session, "resume", now=NOW + timedelta(minutes=35))
        self.action(session, "finish", now=NOW + timedelta(minutes=35))
        self.assertEqual(StudyLog.objects.get().minutes, 25)

    def test_finish_under_one_minute_does_not_create_zero_log(self):
        session = self.start()
        self.action(session, "finish", now=NOW + timedelta(seconds=59))
        self.assertEqual(StudyLog.objects.count(), 0)
        self.assertEqual(self.start().status, FocusSession.Status.RUNNING)

    def test_finish_at_one_minute_logs_once_and_never_changes_task_progress(self):
        session = self.start()
        self.action(session, "finish", notes="Học đúng một phút", now=NOW + timedelta(seconds=60))
        self.action(session, "finish", now=NOW + timedelta(minutes=10))
        self.assertEqual(StudyLog.objects.count(), 1)
        log = StudyLog.objects.get()
        self.assertEqual((log.minutes, log.notes, log.source), (1, "Học đúng một phút", "pomodoro"))
        self.task.refresh_from_db()
        self.assertEqual((self.task.remaining_minutes, self.task.status), (120, Task.Status.TODO))

    def test_cancel_discards_elapsed_and_rejects_later_finish(self):
        session = self.start()
        self.action(session, "cancel", now=NOW + timedelta(minutes=12))
        self.action(session, "cancel", now=NOW + timedelta(minutes=15))
        with self.assertRaises(FocusError):
            self.action(session, "finish")
        self.assertFalse(StudyLog.objects.exists())

    def test_break_requires_finished_work_and_is_not_logged(self):
        session = self.start()
        with self.assertRaises(FocusError):
            self.action(session, "break")
        self.action(session, "finish", now=NOW + timedelta(minutes=25))
        rest = self.action(session, "break", now=NOW + timedelta(minutes=25))
        self.assertEqual((rest.phase, rest.duration_seconds), ("break", 300))
        self.assertEqual(self.action(session, "break").pk, rest.pk)
        self.action(rest, "finish", now=NOW + timedelta(minutes=30))
        self.assertEqual(StudyLog.objects.count(), 1)
        with self.assertRaises(FocusError):
            self.action(rest, "break")

    def test_break_cannot_start_while_another_session_is_active(self):
        session = self.start()
        self.action(session, "finish", now=NOW + timedelta(minutes=1))
        self.start(now=NOW + timedelta(minutes=2))
        with self.assertRaises(FocusError):
            self.action(session, "break", now=NOW + timedelta(minutes=3))

    def test_timer_survives_task_deletion_and_retains_labels(self):
        session = self.start()
        self.task.delete()
        self.action(session, "finish", now=NOW + timedelta(minutes=3))
        log = StudyLog.objects.get()
        session.refresh_from_db()
        self.assertIsNone(session.task_id)
        self.assertEqual((log.task_id, log.task_title, log.subject_label), (None, "Bài Python", "Python — HK1"))
        self.assertEqual(self.action(session, "break").task_id, None)

    def test_study_log_deletion_does_not_recreate_it_on_repeated_finish(self):
        session = self.start()
        self.action(session, "finish", now=NOW + timedelta(minutes=3))
        StudyLog.objects.get().delete()
        self.action(session, "finish", now=NOW + timedelta(minutes=5))
        self.assertEqual(StudyLog.objects.count(), 0)

    def test_database_enforces_single_active_and_valid_state_and_durations(self):
        session = self.start()
        for fields in ({"elapsed_seconds": 1501}, {"resumed_at": None}, {"duration_seconds": 0}):
            with self.assertRaises(IntegrityError), transaction.atomic():
                FocusSession.objects.filter(pk=session.pk).update(**fields)
        with self.assertRaises(IntegrityError), transaction.atomic():
            FocusSession.objects.create(owner=self.owner, task=self.task, task_title="Duplicate", resumed_at=NOW)
        with self.assertRaises(IntegrityError), transaction.atomic():
            StudyLog.objects.create(owner=self.owner, task_title="Invalid", minutes=0)

    def test_manual_log_idempotent_and_validates_ownership_date_and_minutes(self):
        data = self.log_data()
        log = add_manual_log(self.owner, data)
        self.assertEqual(add_manual_log(self.owner, data).pk, log.pk)
        self.assertEqual(StudyLog.objects.count(), 1)
        for values in ({"minutes": 0}, {"minutes": 1441}, {"studied_on": date(2026, 11, 14)}):
            with self.assertRaises(ValidationError):
                add_manual_log(self.owner, self.log_data(**values))
        with self.assertRaises(Task.DoesNotExist):
            add_manual_log(self.owner, self.log_data(task=self.foreign_task))

    def test_model_validation_rejects_foreign_task_timer_or_previous_work(self):
        other = start_work(self.other, self.foreign_task.pk, uuid.uuid4())
        FocusSession(owner=self.owner, task=self.task, task_title="Valid", resumed_at=NOW).full_clean()
        for values in ({"task": self.foreign_task}, {"previous_work": other, "phase": "break"}):
            candidate = FocusSession(owner=self.owner, task=self.task, task_title="Invalid", resumed_at=NOW)
            for field, value in values.items():
                setattr(candidate, field, value)
            with self.assertRaises(ValidationError):
                candidate.full_clean()
        for field, value in (("task", self.foreign_task), ("focus_session", other)):
            log = StudyLog(owner=self.owner, task=self.task, task_title="Title", minutes=1)
            setattr(log, field, value)
            with self.assertRaises(ValidationError):
                log.full_clean()

    def test_start_and_log_forms_only_accept_owned_tasks(self):
        self.assertFalse(FocusStartForm({"task": self.foreign_task.pk, "request_key": uuid.uuid4()}, user=self.owner).is_valid())
        self.assertFalse(FocusStartForm({"task": self.done.pk, "request_key": uuid.uuid4()}, user=self.owner).is_valid())
        form = StudyLogForm({"task": self.foreign_task.pk, "studied_on": "2026-11-13", "minutes": 30, "entry_key": uuid.uuid4()}, user=self.owner)
        self.assertFalse(form.is_valid())

    def test_range_rejects_invalid_dates_order_future_and_over_366_days(self):
        for start, end in (("bad", "2026-11-13"), ("2026-11-14", "2026-11-13"),
                           ("2026-11-13", "2026-11-14"), ("2024-01-01", "2026-11-13"), ("0001-01-01", "9999-12-31")):
            self.assertFalse(LogRangeForm({"start": start, "end": end}).is_valid())
        self.assertTrue(LogRangeForm({"start": "2026-11-13", "end": "2026-11-13"}).is_valid())

    def test_statistics_exact_totals_days_subjects_sources_and_empty_days(self):
        add_manual_log(self.owner, self.log_data(minutes=30))
        add_manual_log(self.owner, self.log_data(minutes=20, studied_on=date(2026, 11, 12)))
        session = self.start()
        self.action(session, "finish", now=NOW + timedelta(minutes=25))
        add_manual_log(self.other, self.log_data(task=self.foreign_task, minutes=90))
        result = build_statistics(StudyLog.objects.filter(owner=self.owner), date(2026, 11, 11), date(2026, 11, 13))
        self.assertEqual(result["totals"], {"minutes": 75, "entries": 3})
        self.assertEqual([d["minutes"] for d in result["days"]], [0, 20, 55])
        self.assertEqual(result["subjects"][0]["minutes"], 75)
        self.assertEqual((result["study_days"], result["daily_average"]), (2, 25.0))
        self.assertEqual({r["source"]: r["minutes"] for r in result["sources"]}, {"manual": 50, "pomodoro": 25})

    def test_empty_statistics_return_zero_without_division_error(self):
        result = build_statistics(StudyLog.objects.none(), NOW.date(), NOW.date())
        self.assertEqual((result["totals"]["minutes"], result["daily_average"], result["study_days"]), (0, 0, 0))
        self.assertEqual(result["days"][0]["width"], 0)

    def test_home_start_state_refresh_and_json_are_read_only_for_get(self):
        home = reverse("focus:home")
        self.assertContains(self.client.get(home), "Bắt đầu học 25 phút")
        self.assertEqual(FocusSession.objects.count(), 0)
        key = uuid.uuid4()
        response = self.client.post(home, {"task": self.task.pk, "request_key": key, "owner": self.other.pk, "duration_seconds": 1})
        session = FocusSession.objects.get()
        self.assertRedirects(response, reverse("focus:session", args=[session.pk]))
        self.assertEqual((session.owner, session.duration_seconds), (self.owner, 1500))
        self.assertContains(self.client.get(home), "Tiếp tục phiên hiện tại")
        with patch("focus.services.timezone.now", return_value=NOW + timedelta(minutes=30)):
            state = self.client.get(reverse("focus:state", args=[session.pk]))
            self.assertEqual(state.json()["remaining"], 0)
            self.assertEqual(state["Cache-Control"], "no-store")
            self.assertContains(self.client.get(response.url), "Lưu và kết thúc phiên học")
        session.refresh_from_db()
        self.assertEqual((session.status, session.elapsed_seconds), ("running", 0))
        self.assertEqual(StudyLog.objects.count(), 0)

    def test_action_routes_are_post_only_and_ignore_forged_clock_or_owner(self):
        session = self.start()
        for action in ("pause", "resume", "finish", "cancel", "break"):
            self.assertEqual(self.client.get(reverse(f"focus:{action}", args=[session.pk])).status_code, 405)
        with patch("focus.services.timezone.now", return_value=NOW + timedelta(minutes=2)):
            response = self.client.post(reverse("focus:finish", args=[session.pk]), {"elapsed_seconds": 999999, "owner": self.other.pk, "notes": "Đã học"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual((StudyLog.objects.get().owner, StudyLog.objects.get().minutes), (self.owner, 2))
        self.assertEqual(self.client.post(reverse("focus:finish", args=[session.pk])).status_code, 302)
        self.assertEqual(StudyLog.objects.count(), 1)

    def test_finish_rejects_oversized_notes_and_invalid_actions_render_error(self):
        session = self.start()
        self.assertEqual(self.client.post(reverse("focus:finish", args=[session.pk]), {"notes": "x" * 1001}).status_code, 400)
        self.assertEqual(self.client.post(reverse("focus:break", args=[session.pk])).status_code, 409)
        session.refresh_from_db()
        self.assertEqual(session.status, "running")

    def test_manual_log_crud_and_pomodoro_edits_only_notes(self):
        payload = {"task": self.task.pk, "studied_on": "2026-11-13", "minutes": 30, "notes": "Manual", "entry_key": uuid.uuid4(), "source": "pomodoro", "owner": self.other.pk}
        create = reverse("focus:log_create")
        self.assertEqual(self.client.post(create, payload).status_code, 302)
        self.assertEqual(self.client.post(create, payload).status_code, 302)
        log = StudyLog.objects.get()
        self.assertEqual((log.source, log.owner), ("manual", self.owner))
        update = reverse("focus:log_update", args=[log.pk])
        self.assertEqual(self.client.post(update, {**payload, "minutes": 40}).status_code, 302)
        log.refresh_from_db()
        self.assertEqual(log.minutes, 40)
        session = self.start()
        self.action(session, "finish", now=NOW + timedelta(minutes=25))
        automatic = StudyLog.objects.get(focus_session=session)
        self.assertEqual(self.client.post(reverse("focus:log_update", args=[automatic.pk]), {"minutes": 1400, "source": "manual", "studied_on": "2026-01-01", "notes": "Sửa ghi chú"}).status_code, 302)
        automatic.refresh_from_db()
        self.assertEqual((automatic.minutes, automatic.source, automatic.studied_on, automatic.notes), (25, "pomodoro", NOW.date(), "Sửa ghi chú"))
        delete = reverse("focus:log_delete", args=[log.pk])
        self.assertEqual(self.client.get(delete).status_code, 200)
        self.assertTrue(StudyLog.objects.filter(pk=log.pk).exists())
        self.assertEqual(self.client.post(delete).status_code, 302)
        self.assertFalse(StudyLog.objects.filter(pk=log.pk).exists())

    def test_log_and_statistics_filters_and_pagination_keep_dates(self):
        for _ in range(21):
            add_manual_log(self.owner, self.log_data())
        response = self.client.get(reverse("focus:logs"))
        self.assertEqual(len(response.context["logs"]), 20)
        self.assertEqual(response.context["filter_query"], "start=2026-11-07&end=2026-11-13")
        page = self.client.get(reverse("focus:logs"), {"start": "2026-11-07", "end": "2026-11-13", "page": 2})
        self.assertEqual(len(page.context["logs"]), 1)
        self.assertEqual(page.context["filter_query"].count("start="), 1)
        stats = self.client.get(reverse("focus:statistics"), {"start": "2026-11-13", "end": "2026-11-13"})
        self.assertEqual(stats.context["totals"]["minutes"], 630)
        for name in ("logs", "statistics"):
            invalid = self.client.get(reverse(f"focus:{name}"), {"start": "bad", "end": "bad"})
            self.assertEqual(invalid.status_code, 200)
            self.assertTrue(invalid.context["range_form"].errors)

    def test_private_routes_require_login_and_reject_foreign_ids(self):
        session = self.start()
        log = add_manual_log(self.owner, self.log_data())
        routes = [("session", session.pk), ("state", session.pk), ("log_update", log.pk), ("log_delete", log.pk)]
        self.client.logout()
        for name in ("home", "logs", "statistics", "log_create"):
            self.assertEqual(self.client.get(reverse(f"focus:{name}")).status_code, 302)
        for name, pk in routes:
            self.assertEqual(self.client.get(reverse(f"focus:{name}", args=[pk])).status_code, 302)
        self.client.force_login(self.other)
        for name, pk in routes:
            self.assertEqual(self.client.get(reverse(f"focus:{name}", args=[pk])).status_code, 404)
        for action in ("pause", "resume", "finish", "cancel", "break"):
            self.assertEqual(self.client.post(reverse(f"focus:{action}", args=[session.pk])).status_code, 404)
        self.assertNotContains(self.client.get(reverse("focus:logs")), "Bài Python")
        self.assertEqual(self.client.get(reverse("focus:statistics")).context["totals"]["minutes"], 0)

    def test_csrf_protects_all_timer_and_log_mutations(self):
        session = self.start()
        log = add_manual_log(self.owner, self.log_data())
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        urls = [reverse("focus:home"), reverse("focus:log_create"), reverse("focus:log_update", args=[log.pk]), reverse("focus:log_delete", args=[log.pk])]
        urls += [reverse(f"focus:{action}", args=[session.pk]) for action in ("pause", "resume", "finish", "cancel", "break")]
        for url in urls:
            self.assertEqual(client.post(url).status_code, 403)

    def test_deleted_task_keeps_manual_history_and_note_edit_and_statistics(self):
        log = add_manual_log(self.owner, self.log_data())
        self.task.delete()
        log.refresh_from_db()
        self.assertIsNone(log.task_id)
        self.assertEqual((log.task_title, log.subject_label), ("Bài Python", "Python — HK1"))
        self.assertEqual(self.client.post(reverse("focus:log_update", args=[log.pk]), {"studied_on": "2026-11-13", "minutes": 35, "notes": "Giữ lịch sử"}).status_code, 302)
        self.assertEqual(self.client.get(reverse("focus:statistics")).context["totals"]["minutes"], 35)

    def test_sqlite_busy_response_is_recoverable_and_does_not_claim_success(self):
        session = self.start()
        with patch("focus.views.timer_action", side_effect=OperationalError("database is locked")):
            response = self.client.post(reverse("focus:pause", args=[session.pk]))
        self.assertContains(response, "Hãy tải lại trạng thái rồi thử lại", status_code=409)
        session.refresh_from_db()
        self.assertEqual(session.status, "running")
