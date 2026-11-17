import hashlib
import json
import re
import uuid
from datetime import timedelta
from html.parser import HTMLParser
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from focus.models import FocusSession, StudyLog
from insights.data import baseline_report, build_snapshot, fingerprint
from insights.models import InsightReport
from integrations.models import CalendarConnection, CalendarSyncJob
from planner.models import BusyEvent, StudyPlan, StudySession
from studies.models import Material, Subject, Task


class PageMarkup(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.mains = []
        self.headers = 0
        self.splits = 0
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        classes = dict(attrs).get("class", "").split()
        if tag == "main":
            self.mains.append(classes)
        self.headers += tag == "header" and "page-header" in classes
        self.splits += "split" in classes


class PageLayoutTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("layout-owner", first_name="An")
        now = timezone.now()
        week = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
        cls.subject = Subject.objects.create(owner=cls.user, name="Python")
        cls.task = Task.objects.create(owner=cls.user, subject=cls.subject, title="Việc của tôi",
                                       deadline=now + timedelta(days=3), estimated_minutes=90, remaining_minutes=90)
        cls.material = Material.objects.create(owner=cls.user, title="Tài liệu", url="https://example.test/lesson")
        cls.plan = StudyPlan.objects.create(owner=cls.user, week_start=week, applied_at=now)
        cls.session = StudySession.objects.create(owner=cls.user, plan=cls.plan, task=cls.task,
                                                  starts_at=now + timedelta(days=1), ends_at=now + timedelta(days=1, hours=1))
        cls.busy = BusyEvent.objects.create(owner=cls.user, title="Lên lớp", starts_at=now, ends_at=now + timedelta(hours=1))
        cls.focus = FocusSession.objects.create(owner=cls.user, task_title=cls.task.title, task=cls.task,
                                                status="finished", finished_at=now)
        cls.log = StudyLog.objects.create(owner=cls.user, task_title=cls.task.title, task=cls.task, minutes=25)
        connection = CalendarConnection.objects.create(owner=cls.user)
        cls.job = CalendarSyncJob.objects.create(connection=connection, generation=connection.generation,
                                                 week_start=week, input_hash="layout", status="success")
        snapshot = build_snapshot(cls.user)
        cls.report = InsightReport.objects.create(owner=cls.user, request_key=uuid.uuid4(), model_name="layout",
                                                   snapshot=snapshot, input_hash=fingerprint(snapshot),
                                                   status="success", result=baseline_report(snapshot))

    def setUp(self):
        self.client.force_login(self.user)

    def assert_page(self, name, kind="", pk=None, split=False):
        response = self.client.get(reverse(name, args=[pk] if pk else []))
        self.assertEqual(response.status_code, 200)
        page = PageMarkup(response.content.decode())
        self.assertEqual(len(page.mains), 1)
        self.assertIn("page", page.mains[0])
        self.assertEqual([c for c in page.mains[0] if c.startswith("page--")], [kind] if kind else [])
        self.assertEqual(page.headers, 0 if name == "planner:week" else 1)
        self.assertEqual(page.splits, int(split))
        if name == "planner:week":
            self.assertIn("calendar-container", page.mains[0])
        return response

    def test_all_authenticated_pages_have_one_main_of_the_expected_type(self):
        standard = (
            ("core:home", None), ("planner:week", None), ("planner:plan_detail", self.plan.pk),
            ("planner:alerts", None), ("planner:busy_list", None),
            ("studies:task_list", None), ("studies:subject_list", None), ("studies:material_list", None),
            ("studies:task_create", None), ("studies:task_update", self.task.pk), ("studies:task_progress", self.task.pk),
            ("studies:subject_create", None), ("studies:subject_update", self.subject.pk),
            ("studies:material_create", None), ("studies:material_update", self.material.pk),
            ("focus:session", self.focus.pk), ("focus:statistics", None), ("focus:logs", None),
            ("insights:home", None), ("insights:report", self.report.pk),
            ("notifications:inbox", None), ("notifications:email_history", None), ("integrations:job", self.job.pk),
        )
        narrow = (
            ("planner:busy_create", None), ("planner:busy_update", self.busy.pk), ("planner:busy_delete", self.busy.pk),
            ("planner:session_move", self.session.pk), ("planner:session_record", self.session.pk),
            ("focus:log_create", None), ("focus:log_update", self.log.pk), ("focus:log_delete", self.log.pk),
            ("studies:task_delete", self.task.pk), ("studies:subject_delete", self.subject.pk),
            ("studies:material_delete", self.material.pk),
        )
        for name, pk in standard + narrow:
            with self.subTest(name=name):
                self.assert_page(name, "page--narrow" if (name, pk) in narrow else "", pk=pk)
        for name in ("planner:plan_generate", "planner:preferences", "focus:home", "accounts:profile",
                     "accounts:password_change", "notifications:preferences", "integrations:google"):
            with self.subTest(name=name):
                self.assert_page(name, split=True)

    def test_public_pages_use_auth_or_standard_frame_without_private_navigation(self):
        self.client.logout()
        for name in ("core:home", "accounts:login", "accounts:register"):
            with self.subTest(name=name):
                response = self.assert_page(name, "" if name == "core:home" else "page--auth")
                self.assertNotContains(response, 'aria-label="Điều hướng chính"')

    @override_settings(AUTH_PASSWORD_VALIDATORS=[])
    def test_password_without_existing_rules_uses_full_width_form(self):
        response = self.assert_page("accounts:password_change")
        self.assertContains(response, 'class="account-form form-grid"')
        self.assertNotContains(response, "Quy tắc mật khẩu")

    def test_invalid_posts_keep_narrow_frame_csrf_and_entered_values(self):
        response = self.client.post(reverse("planner:busy_create"), {"title": "Lịch đã nhập"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("page--narrow", PageMarkup(response.content.decode()).mains[0])
        self.assertContains(response, "Lịch đã nhập")
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertFalse(BusyEvent.objects.filter(owner=self.user, title="Lịch đã nhập").exists())

    def test_relocated_help_text_keeps_accessible_ids_and_plan_mode_sources(self):
        response = self.assert_page("planner:preferences", split=True)
        form = response.context["form"]
        for field in form:
            if field.help_text:
                self.assertContains(response, f'id="{field.auto_id}_helptext"', count=1)
        response = self.assert_page("planner:plan_generate", split=True)
        for marker in ("plan-mode-help", "plan-mode-add", "plan-mode-replace"):
            self.assertContains(response, f'id="{marker}"', count=1)
        markup = response.content.decode()
        self.assertLess(markup.index('id="id_week"'), markup.index("Chọn tuần hiện tại hoặc tương lai"))
        self.assertLess(markup.index("Chọn tuần hiện tại hoặc tương lai"), markup.index('id="id_mode"'))


class ThemeAssetTests(SimpleTestCase):
    def test_local_fonts_match_sources_and_css_has_no_cdn_dependency(self):
        folder = Path(settings.BASE_DIR) / "static/fonts"
        records = json.loads((folder / "sources.json").read_text())
        self.assertEqual(len(records), 6)
        for record in records:
            data = (folder / record["file"]).read_bytes()
            self.assertEqual(data[:4], b"wOF2")
            self.assertEqual(hashlib.sha256(data).hexdigest(), record["sha256"])
        css = (folder / "fonts.css").read_text()
        self.assertNotIn("https://", css)
        self.assertEqual(css.count("font-display: swap"), 6)
        self.assertEqual(css.count("unicode-range:"), 6)

    def test_text_token_pairs_meet_normal_text_contrast(self):
        css = (Path(settings.BASE_DIR) / "static/css/tokens.css").read_text()
        colors = dict(re.findall(r"--([\w-]+):\s*(#[0-9A-Fa-f]{6})", css))

        def luminance(value):
            rgb = [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            rgb = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
            return sum(v * w for v, w in zip(rgb, (.2126, .7152, .0722)))

        for foreground, background in (("text", "surface"), ("muted", "surface"), ("muted", "bg"),
                                       ("button-ink", "pine"), ("pine-hover", "pine-soft"),
                                       ("amber-ink", "amber-soft"), ("coral-ink", "coral-soft"), ("sky-ink", "sky-soft")):
            with self.subTest(foreground=foreground, background=background):
                a, b = sorted((luminance(colors[foreground]), luminance(colors[background])))
                self.assertGreaterEqual((b + .05) / (a + .05), 4.5)
