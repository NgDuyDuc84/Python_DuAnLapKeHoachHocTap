from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.test_navigation import NavigationParser
from focus.forms import FocusStartForm
from notifications.models import ReminderPreference
from planner.models import BusyEvent, StudyPlan, StudySession
from studies.models import Subject, Task


class UiCleanupTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("ui-cleanup", email="ui@example.test")
        now = timezone.now()
        cls.task = Task.objects.create(
            owner=cls.user, title="Việc của tôi", deadline=now + timedelta(days=7),
            estimated_minutes=50, remaining_minutes=50,
        )
        today = timezone.localdate()
        cls.plan = StudyPlan.objects.create(
            owner=cls.user, week_start=today - timedelta(days=today.weekday()), applied_at=now,
        )
        cls.session = StudySession.objects.create(
            owner=cls.user, plan=cls.plan, task=cls.task,
            starts_at=now + timedelta(hours=1), ends_at=now + timedelta(hours=2),
        )
        cls.busy = BusyEvent.objects.create(
            owner=cls.user, title="Lịch bận", starts_at=now, ends_at=now + timedelta(hours=1),
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_all_planner_pages_use_header_without_section_tabs(self):
        pages = (
            ("week", [], "week"),
            ("plan_generate", [], "plan_generate"),
            ("plan_detail", [self.plan.pk], "plan_generate"),
            ("alerts", [], "alerts"),
            ("preferences", [], "preferences"),
            ("busy_list", [], "busy_list"),
            ("busy_create", [], "busy_list"),
            ("busy_update", [self.busy.pk], "busy_list"),
            ("busy_delete", [self.busy.pk], "busy_list"),
            ("session_move", [self.session.pk], "week"),
            ("session_record", [self.session.pk], "week"),
        )
        for name, args, active in pages:
            with self.subTest(name=name):
                response = self.client.get(reverse("planner:" + name, args=args))
                self.assertEqual(response.status_code, 200)
                markup = response.content.decode()
                self.assertNotContains(response, 'class="section-tabs"')
                self.assertNotContains(response, 'aria-label="Quản lý lịch"')
                self.assertTemplateNotUsed(response, "components/section_tabs.html")
                main = NavigationParser(markup, "Điều hướng chính").links
                self.assertEqual([link["href"] for link in main], [reverse(target) for target in (
                    "core:home", "planner:week", "planner:plan_generate", "planner:busy_list",
                    "planner:preferences", "studies:task_list", "focus:home", "focus:statistics", "planner:alerts",
                )])
                self.assertEqual([link["href"] for link in main if link.get("aria-current") == "page"],
                                 [reverse("planner:" + active)])
                if name != "week":
                    self.assertTemplateUsed(response, "components/page_header.html")
                    self.assertContains(response, '<header class="page-header">', count=1)
                    self.assertNotContains(response, 'class="eyebrow"')
                self.assertTemplateNotUsed(response, "components/settings_layout.html")
        week = self.client.get(reverse("planner:week"))
        self.assertNotContains(week, 'aria-label="Quản lý lịch"')
        self.assertNotContains(week, 'class="page-header"')

    def test_profile_hides_non_staff_role_and_learning_cta(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertNotContains(response, "Vai trò")
        self.assertNotContains(response, "Vào không gian học tập")
        self.assertContains(response, "Đổi mật khẩu")
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        self.assertContains(self.client.get(reverse("accounts:profile")), "Vai trò")

    @override_settings(DEBUG=False, GOOGLE_CLIENT_ID="", GOOGLE_TOKEN_ENCRYPTION_KEY="",
                       EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend")
    def test_ordinary_users_get_friendly_notices_without_technical_details(self):
        for name in ("integrations:google", "notifications:preferences", "notifications:email_history"):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                for technical in ("README.md", "OAuth Client", "terminal", "worker", "dịch vụ nền"):
                    self.assertNotContains(response, technical)
                self.assertContains(response, "chưa khả dụng")
        response = self.client.get(reverse("integrations:google"))
        self.assertContains(response, '<button class="button" type="button" disabled>Kết nối Google</button>', html=True)

    @override_settings(GOOGLE_CLIENT_ID="", GOOGLE_TOKEN_ENCRYPTION_KEY="",
                       EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend")
    def test_technical_details_are_visible_for_staff_or_debug(self):
        for staff, debug, visible in ((False, False, False), (True, False, True), (False, True, True)):
            with self.subTest(staff=staff, debug=debug), override_settings(DEBUG=debug):
                self.user.is_staff = staff
                self.user.save(update_fields=["is_staff"])
                google = self.client.get(reverse("integrations:google"))
                reminders = self.client.get(reverse("notifications:preferences"))
                self.assertEqual("README.md" in google.content.decode(), visible)
                self.assertEqual("terminal" in reminders.content.decode(), visible)
                self.assertEqual("dịch vụ nền" in reminders.content.decode(), visible)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend")
    def test_disabled_email_field_preserves_saved_opt_in(self):
        preference = ReminderPreference.objects.create(owner=self.user, email_enabled=True)
        response = self.client.get(reverse("notifications:preferences"))
        self.assertContains(response, '<fieldset class="email-unavailable" disabled aria-describedby="email-availability">')
        self.assertContains(response, '<input type="hidden" name="email_enabled" value="on">', html=True)
        response = self.client.post(reverse("notifications:preferences"), {
            "in_app_enabled": "on", "email_enabled": "on", "deadline_minutes": 60, "session_minutes": 5,
        })
        self.assertRedirects(response, reverse("notifications:preferences"))
        preference.refresh_from_db()
        self.assertTrue(preference.email_enabled)
        self.assertEqual(preference.deadline_minutes, 60)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend")
    def test_real_email_backend_keeps_checkbox_available(self):
        response = self.client.get(reverse("notifications:preferences"))
        self.assertNotContains(response, '<fieldset class="email-unavailable"')
        self.assertContains(response, 'name="email_enabled"')

    def test_subject_tabs_and_semester_have_clear_labels(self):
        Subject.objects.create(owner=self.user, name="Toán", semester="7")
        Subject.objects.create(owner=self.user, name="Văn", semester="Học kỳ 8")
        response = self.client.get(reverse("studies:subject_list"))
        self.assertContains(response, "Học kỳ 7")
        self.assertContains(response, "Học kỳ 8")
        self.assertNotContains(response, "Học kỳ Học kỳ")
        tabs = NavigationParser(response.content.decode(), "Nội dung học tập").links
        self.assertEqual([link["href"] for link in tabs], [reverse("studies:" + name) for name in (
            "task_list", "subject_list", "material_list",
        )])
        self.assertTemplateUsed(response, "components/section_tabs.html")

    def test_focus_empty_label_keeps_owned_unfinished_choices(self):
        other = get_user_model().objects.create_user("ui-cleanup-other")
        Task.objects.create(owner=other, title="Việc người khác", deadline=timezone.now(), estimated_minutes=10, remaining_minutes=10)
        Task.objects.create(owner=self.user, title="Đã xong", deadline=timezone.now(), estimated_minutes=10, remaining_minutes=0, status="done")
        field = FocusStartForm(user=self.user).fields["task"]
        self.assertEqual(field.empty_label, "Chọn công việc…")
        self.assertEqual(list(field.queryset), [self.task])
        self.assertContains(self.client.get(reverse("focus:home")), "Chọn công việc…")

    def test_plan_explanations_use_side_card_and_links_stay_in_planner(self):
        response = self.client.get(reverse("planner:plan_generate"))
        markup = response.content.decode()
        self.assertLess(markup.index('id="id_mode"'), markup.index('<details class="explanation">'))
        self.assertContains(response, '<h2>Cách hệ thống xếp lịch</h2>', html=True)
        self.assertContains(response, '<summary>Xem chi tiết</summary>', html=True)
        self.assertContains(response, 'class="split"')
        self.assertContains(response, 'id="plan-mode-help"')
        self.assertContains(response, 'href="' + reverse("planner:preferences") + '">Điều chỉnh giờ học')
        response = self.client.post(reverse("planner:plan_generate"), {"mode": "replace", "week": "invalid"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<p id="plan-mode-help" class="field-help" aria-live="polite">Thay các buổi tự động')
        response = self.client.get(reverse("planner:alerts"))
        self.assertContains(response, '<summary>Cách đọc cảnh báo</summary>', html=True)
        self.assertContains(response, 'href="' + reverse("notifications:preferences") + '">Cài đặt nhắc việc')
