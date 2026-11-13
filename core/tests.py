import json
import os
from pathlib import Path
import subprocess
import sys
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.db import OperationalError
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.views.defaults import server_error
from django.utils import timezone

from focus.models import StudyLog
from insights.data import build_snapshot
from insights.models import InsightReport
from integrations.models import CalendarConnection
from notifications.models import ReminderPreference
from planner.models import StudyPlan, StudySession
from studies.models import Material, Subject, Task


class ReadinessTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("demo-test", password="Synthetic-test-password-11")

    def seed(self):
        output = StringIO()
        call_command("seed_demo", username=self.user.username, stdout=output)
        return output.getvalue()

    def test_demo_is_owned_valid_and_does_not_call_external_services(self):
        with patch("requests.sessions.Session.request") as external:
            output = self.seed()
        external.assert_not_called()
        self.assertIn("Demo created", output)
        self.assertEqual(Subject.objects.filter(owner=self.user).count(), 2)
        self.assertEqual(Task.objects.filter(owner=self.user).count(), 5)
        self.assertEqual(Material.objects.filter(owner=self.user).count(), 2)
        self.assertEqual(StudySession.objects.filter(owner=self.user).count(), 3)
        self.assertEqual(sum(StudyLog.objects.filter(owner=self.user).values_list("minutes", flat=True)), 175)
        self.assertFalse(ReminderPreference.objects.get(owner=self.user).email_enabled)
        self.assertEqual(CalendarConnection.objects.count(), 0)
        self.assertEqual(InsightReport.objects.count(), 0)
        for model in (Task, StudySession, StudyLog):
            for obj in model.objects.all():
                obj.full_clean()
        payload = build_snapshot(self.user)["payload"]
        self.assertEqual(payload["facts"]["H01"]["minutes"], 175)

    def test_demo_is_idempotent_and_keeps_login_credentials(self):
        password_hash = self.user.password
        self.seed()
        before = list(Task.objects.values_list("pk", "remaining_minutes"))
        self.assertIn("already exists", self.seed())
        self.assertEqual(list(Task.objects.values_list("pk", "remaining_minutes")), before)
        self.user.refresh_from_db()
        self.assertEqual(self.user.password, password_hash)

    def test_demo_refuses_nonempty_staff_inactive_and_missing_accounts(self):
        Subject.objects.create(owner=self.user, name="Existing personal subject")
        with self.assertRaisesMessage(CommandError, "not empty"):
            self.seed()
        self.assertEqual(Subject.objects.count(), 1)
        for username, attrs in [("missing", None), ("staff", {"is_staff": True}), ("inactive", {"is_active": False})]:
            if attrs:
                get_user_model().objects.create_user(username, **attrs)
            with self.assertRaises(CommandError):
                call_command("seed_demo", username=username, stdout=StringIO())
        self.assertEqual(Task.objects.count(), 0)

    def test_demo_rolls_back_if_creation_fails(self):
        with patch("core.management.commands.seed_demo.StudyLog.objects.create", side_effect=ValueError("Synthetic failure")):
            with self.assertRaises(ValueError):
                self.seed()
        self.assertEqual(Subject.objects.count(), 0)
        self.assertEqual(Task.objects.count(), 0)
        self.assertEqual(StudyPlan.objects.count(), 0)

    def test_demo_does_not_touch_other_users(self):
        other = get_user_model().objects.create_user("other-demo")
        subject = Subject.objects.create(owner=other, name="Other account")
        self.seed()
        subject.refresh_from_db()
        self.assertEqual(subject.name, "Other account")
        self.assertEqual(Subject.objects.filter(owner=other).count(), 1)

    def test_demo_works_at_week_and_year_boundary(self):
        from datetime import datetime
        day = timezone.make_aware(datetime(2027, 12, 31, 23))
        with patch("core.management.commands.seed_demo.timezone.localdate", return_value=day.date()):
            self.seed()
        plan = StudyPlan.objects.get()
        self.assertEqual(plan.week_start.weekday(), 0)
        for session in StudySession.objects.all():
            self.assertTrue(plan.week_start <= timezone.localdate(session.starts_at) <= plan.week_end)

    def test_health_checks_database_without_exposing_details(self):
        response = self.client.get(reverse("core:health"))
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertEqual(response["Cache-Control"], "no-store")
        with patch("core.views.connection.cursor", side_effect=OperationalError("PRIVATE_DATABASE_PASSWORD")):
            response = self.client.get(reverse("core:health"))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})
        self.assertNotContains(response, "PRIVATE", status_code=503)
        self.assertEqual(self.client.post(reverse("core:health")).status_code, 405)

    def test_home_cta_matches_authentication_state(self):
        self.assertContains(self.client.get(reverse("core:home")), "Bắt đầu lập kế hoạch")
        self.client.force_login(self.user)
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "Mở lịch học của bạn")
        self.assertNotContains(response, "Đăng nhập để quản lý")

    @override_settings(DEBUG=False)
    def test_errors_have_navigation_and_no_internal_details(self):
        response = self.client.get("/missing-synthetic-page/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Về trang chủ", status_code=404)
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Cần tải lại trang", status_code=403)
        response = server_error(RequestFactory().get("/"))
        self.assertEqual(response.status_code, 500)
        self.assertIn("Vui lòng thử lại sau", response.content.decode())
        self.assertNotIn("Traceback", response.content.decode())


class DeploymentConfigTests(TestCase):
    def run_settings(self, *, module="config.production", **overrides):
        env = {**os.environ,
            "DJANGO_SETTINGS_MODULE": module, "DJANGO_DEBUG": "false",
            "DJANGO_SECRET_KEY": "synthetic-production-config-test-key-84-only-not-a-real-secret",
            "DJANGO_ALLOWED_HOSTS": "study.example.test", "SITE_URL": "https://study.example.test",
            "DATABASE_URL": "postgresql://test:test@127.0.0.1:5432/test",
            **overrides,
        }
        code = (
            "import django,json; django.setup(); from django.conf import settings; "
            "print(json.dumps({'debug':settings.DEBUG,'engine':settings.DATABASES['default']['ENGINE'],"
            "'ssl':settings.DATABASES['default'].get('OPTIONS',{}).get('sslmode'),"
            "'secure_cookie':getattr(settings,'SESSION_COOKIE_SECURE',False),"
            "'https_redirect':getattr(settings,'SECURE_SSL_REDIRECT',False),"
            "'static_backend':settings.STORAGES['staticfiles']['BACKEND']}))"
        )
        return subprocess.run([sys.executable, "-c", code], env=env, cwd=Path(__file__).resolve().parent.parent,
                              capture_output=True, text=True, encoding="utf-8", timeout=20)

    def test_production_requires_postgres_https_hosts_and_private_secret(self):
        for override in (
            {"DJANGO_SECRET_KEY": "short"}, {"DJANGO_SECRET_KEY": "x" * 64},
            {"DJANGO_ALLOWED_HOSTS": "*"}, {"DJANGO_ALLOWED_HOSTS": "other.example.test"},
            {"SITE_URL": "http://study.example.test"}, {"SITE_URL": "https://study.example.test/path"},
            {"DATABASE_URL": ""}, {"DATABASE_URL": "sqlite:///test.sqlite3"},
        ):
            with self.subTest(override=list(override)):
                result = self.run_settings(**override)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("ImproperlyConfigured", result.stderr)

    def test_production_configuration_and_local_ssl_override(self):
        result = self.run_settings()
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["engine"], "django.db.backends.postgresql")
        self.assertEqual(data["ssl"], "require")
        self.assertFalse(data["debug"])
        self.assertTrue(data["secure_cookie"])
        self.assertTrue(data["https_redirect"])
        self.assertIn("CompressedManifest", data["static_backend"])
        result = self.run_settings(DATABASE_URL="postgresql://test:test@127.0.0.1:5432/test?sslmode=disable")
        self.assertEqual(json.loads(result.stdout)["ssl"], "disable")

    def test_local_settings_keep_sqlite_and_http(self):
        result = self.run_settings(module="config.settings", DATABASE_URL="", DJANGO_DEBUG="true")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["engine"], "django.db.backends.sqlite3")
        self.assertFalse(data["secure_cookie"])
        self.assertFalse(data["https_redirect"])

    def test_invalid_database_url_error_does_not_echo_credentials(self):
        result = self.run_settings(DATABASE_URL="unknown://PRIVATE_PASSWORD@host/db")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("PRIVATE_PASSWORD", result.stderr)
