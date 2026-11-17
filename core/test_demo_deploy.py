import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from deploy.demo import main


class DemoProcessTests(SimpleTestCase):
    def setUp(self):
        self.signals = patch("deploy.demo.signal.signal").start()
        self.run = patch("deploy.demo.subprocess.run").start()
        self.spawn = patch("deploy.demo.subprocess.Popen").start()
        self.stop = patch("deploy.demo.Event").start().return_value
        self.stop.is_set.return_value = False
        self.addCleanup(patch.stopall)

    def test_failed_migration_never_starts_web_or_workers(self):
        self.run.side_effect = [None, subprocess.CalledProcessError(1, "migrate")]
        with self.assertRaises(subprocess.CalledProcessError):
            main()
        self.spawn.assert_not_called()

    def test_worker_failure_stops_web_and_other_worker_with_failure_status(self):
        web, reminders, calendar = Mock(), Mock(), Mock()
        web.poll.return_value = calendar.poll.return_value = None
        reminders.poll.return_value = reminders.returncode = 2
        self.spawn.side_effect = [web, reminders, calendar]
        self.stop.wait.return_value = False
        self.assertEqual(main(), 2)
        web.terminate.assert_called_once()
        calendar.terminate.assert_called_once()
        reminders.terminate.assert_not_called()
        for process in (web, reminders, calendar):
            process.wait.assert_called_once()

    def test_shutdown_terminates_children_and_kills_an_unresponsive_child(self):
        processes = [Mock(), Mock(), Mock()]
        for process in processes:
            process.poll.return_value = None
        processes[0].wait.side_effect = [subprocess.TimeoutExpired("web", 5), 0]
        self.spawn.side_effect = processes
        self.stop.wait.return_value = True
        self.assertEqual(main(), 0)
        for process in processes:
            process.terminate.assert_called_once()
        processes[0].kill.assert_called_once()


class RenderSettingsTests(SimpleTestCase):
    def settings_result(self, **overrides):
        env = {**os.environ,
               "DJANGO_SETTINGS_MODULE": "config.render", "DJANGO_DEBUG": "false",
               "DJANGO_SECRET_KEY": "", "DJANGO_ALLOWED_HOSTS": "",
               "SITE_URL": "", "RENDER_EXTERNAL_HOSTNAME": "nhip-hoc-test.onrender.com",
               "RENDER_SECRET_KEY": "synthetic-render-platform-secret-256-bit-value",
               "DATABASE_URL": "postgresql://test:test@localhost/test",
               **overrides}
        # Blank optional overrides should use Render's automatic hostname settings.
        for key in ("DJANGO_SECRET_KEY", "DJANGO_ALLOWED_HOSTS", "SITE_URL"):
            if not env[key]:
                del env[key]
        code = (
            "import django,json; django.setup(); from django.conf import settings; "
            "from django.middleware.security import SecurityMiddleware; "
            "from django.http import HttpResponse; from django.test import RequestFactory; "
            "middleware=SecurityMiddleware(lambda request: HttpResponse()); "
            "factory=RequestFactory(HTTP_HOST=settings.ALLOWED_HOSTS[0]); "
            "print(json.dumps({'hosts':settings.ALLOWED_HOSTS,'site':settings.SITE_URL,"
            "'secret_length':len(settings.SECRET_KEY),'debug':settings.DEBUG,"
            "'health':middleware(factory.get('/health/')).status_code,"
            "'home':middleware(factory.get('/')).status_code,"
            "'secure_cookie':settings.SESSION_COOKIE_SECURE}))"
        )
        return subprocess.run([sys.executable, "-c", code], env=env,
                              cwd=Path(__file__).resolve().parent.parent,
                              capture_output=True, text=True, encoding="utf-8", timeout=20)

    def test_platform_hostname_secret_and_http_probe_keep_normal_pages_secure(self):
        result = self.settings_result()
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["hosts"], ["nhip-hoc-test.onrender.com"])
        self.assertEqual(data["site"], "https://nhip-hoc-test.onrender.com")
        self.assertEqual(data["secret_length"], 64)
        self.assertEqual(data["health"], 200)
        self.assertEqual(data["home"], 301)
        self.assertFalse(data["debug"])
        self.assertTrue(data["secure_cookie"])

    def test_missing_platform_secret_fails_and_explicit_custom_domain_is_preserved(self):
        result = self.settings_result(RENDER_SECRET_KEY="")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ImproperlyConfigured", result.stderr)
        result = self.settings_result(DJANGO_ALLOWED_HOSTS="study.example.test",
                                      SITE_URL="https://study.example.test")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["site"], "https://study.example.test")
