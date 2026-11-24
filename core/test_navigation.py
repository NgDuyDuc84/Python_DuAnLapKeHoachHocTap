from datetime import timedelta
from html.parser import HTMLParser
import re
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import resolve, reverse
from django.utils import timezone

from core.templatetags.navigation import navigation_state
from planner.models import BusyEvent


class NavigationParser(HTMLParser):
    def __init__(self, markup, label):
        super().__init__()
        self.label = label
        self.inside = False
        self.links = []
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "nav" and attrs.get("aria-label") == self.label:
            self.inside = True
        if self.inside and tag == "a":
            self.links.append(attrs)

    def handle_endtag(self, tag):
        if tag == "nav":
            self.inside = False


class NavigationStateTests(SimpleTestCase):
    def test_all_existing_page_names_render_the_expected_main_active_item(self):
        groups = {
            "overview": ("core:home",),
            "planner": (
                "planner:week", "planner:plan_generate", "planner:plan_detail",
                "planner:session_move", "planner:session_record", "planner:session_lock", "planner:plan_apply", "planner:alerts",
                "planner:preferences", "planner:busy_list", "planner:busy_create", "planner:busy_update", "planner:busy_delete",
            ),
            "studies": tuple(f"studies:{name}" for name in (
                "subject_list", "subject_create", "subject_update", "subject_delete",
                "task_list", "task_create", "task_update", "task_delete", "task_progress",
                "material_list", "material_create", "material_update", "material_delete",
            )),
            "focus": ("focus:home", "focus:session"),
            "statistics": (
                "focus:statistics", "focus:logs", "focus:log_create",
                "focus:log_update", "focus:log_delete", "insights:home", "insights:report",
            ),
            "notifications": ("notifications:inbox", "notifications:email_history"),
            "settings": (
                "accounts:profile", "accounts:password_change", "accounts:password_change_done",
                "notifications:preferences",
                "integrations:google", "integrations:job",
            ),
        }
        detail_names = {
            "plan_detail", "plan_apply", "session_move", "session_record", "session_lock", "session", "report", "job",
            "subject_update", "subject_delete", "task_update", "task_delete", "task_progress",
            "material_update", "material_delete", "log_update", "log_delete", "busy_update", "busy_delete",
        }
        for section, names in groups.items():
            for name in names:
                with self.subTest(name=name):
                    args = [1] if name.split(":")[1] in detail_names else []
                    request = RequestFactory().get(reverse(name, args=args))
                    request.resolver_match = resolve(request.path)
                    state = navigation_state(request)
                    self.assertEqual(state["section"], section)
                    markup = render_to_string("base.html", {
                        "request": request,
                        "user": SimpleNamespace(is_authenticated=True, username="learner", is_staff=False),
                    })
                    links = NavigationParser(markup, "Điều hướng chính").links
                    self.assertEqual([link["href"] for link in links], [reverse(target) for target in (
                        "core:home", "planner:week", "planner:plan_generate",
                        "planner:busy_list", "planner:preferences", "studies:task_list", "focus:home", "insights:home", "focus:statistics", "planner:alerts",
                    )])
                    active = [link["href"] for link in links if link.get("aria-current") == "page"]
                    if section == "planner":
                        target = next(target for prefix, target in (
                            ("plan_", "plan_generate"), ("busy_", "busy_list"),
                            ("session_", "week"), ("alerts", "alerts"),
                            ("preferences", "preferences"), ("week", "week"),
                        ) if name.split(":")[1].startswith(prefix))
                        expected = [reverse("planner:" + target)]
                        self.assertEqual(state["tabs"], ())
                    else:
                        targets = {"overview": "core:home", "studies": "studies:task_list",
                                   "focus": "focus:home", "statistics": "focus:statistics"}
                        expected = [reverse(targets[section])] if section in targets else []
                    if name.startswith("insights:"):
                        expected = [reverse("insights:home")]
                    self.assertEqual(active, expected)
                    account_links = re.findall(r'<a class="header-menu-link" href="([^"]+)"([^>]*)>', markup)
                    self.assertEqual([url for url, attrs in account_links], [reverse(target) for target in (
                        "accounts:profile", "notifications:preferences", "integrations:google",
                    )])
                    self.assertEqual([url for url, attrs in account_links if 'aria-current="page"' in attrs],
                                     [reverse(next(tab["url"] for tab in state["settings_tabs"]
                                                   if tab["key"] == state["settings_item"]))]
                                     if section == "settings" else [])
                    if section in ("settings", "notifications"):
                        icon = "account" if section == "settings" else "notifications"
                        self.assertIn(f"header-{icon} is-active", markup)

    def test_error_pages_without_resolver_match_do_not_select_overview(self):
        request = RequestFactory().get("/missing/")
        self.assertEqual(navigation_state(request)["section"], "")
        self.assertEqual(navigation_state(request)["main_item"], "")

    def test_unknown_route_does_not_activate_a_planner_link(self):
        request = RequestFactory().get("/planner/unknown/")
        request.resolver_match = SimpleNamespace(view_name="planner:unknown")
        self.assertEqual(navigation_state(request)["main_item"], "")

    def test_base_does_not_render_private_navigation_for_anonymous_users(self):
        request = RequestFactory().get("/missing/")
        markup = render_to_string("base.html", {"request": request, "user": SimpleNamespace(is_authenticated=False)})
        self.assertEqual(NavigationParser(markup, "Điều hướng chính").links, [])
        self.assertNotIn('aria-label="Menu điều hướng"', markup)


class NavigationPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user("ui-owner")
        cls.other = get_user_model().objects.create_user("ui-other")
        now = timezone.now()
        cls.event = BusyEvent.objects.create(
            owner=cls.owner, title="Lịch bận riêng", starts_at=now, ends_at=now + timedelta(hours=1),
        )

    def setUp(self):
        self.client.force_login(self.owner)

    def test_settings_pages_share_three_tabs_and_keep_forms_and_csrf(self):
        pages = (
            ("accounts:profile", [], "account", False),
            ("accounts:password_change", [], "account", True),
            ("notifications:preferences", [], "reminders", True),
            ("integrations:google", [], "google", False),
        )
        targets = {
            "account": "accounts:profile", "reminders": "notifications:preferences",
            "google": "integrations:google",
        }
        for name, args, active, has_form in pages:
            with self.subTest(name=name):
                response = self.client.get(reverse(name, args=args))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "components/settings_layout.html")
                links = NavigationParser(response.content.decode(), "Cài đặt").links
                self.assertEqual(len(links), 3)
                self.assertNotContains(response, "settings-sidebar")
                self.assertTemplateUsed(response, "components/page_header.html")
                self.assertEqual(
                    [link["href"] for link in links if link.get("aria-current") == "page"],
                    [reverse(targets[active])],
                )
                if has_form:
                    self.assertContains(response, 'name="csrfmiddlewaretoken"', count=2)

    def test_statistics_and_notifications_use_shared_tabs(self):
        for name, label, expected in (
            ("focus:statistics", "Thống kê", "focus:statistics"),
            ("focus:logs", "Thống kê", "focus:logs"),
            ("focus:log_create", "Thống kê", "focus:logs"),
            ("insights:home", "Thống kê", "insights:home"),
            ("notifications:inbox", "Thông báo", "notifications:inbox"),
            ("notifications:email_history", "Thông báo", "notifications:email_history"),
        ):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "components/section_tabs.html")
                links = NavigationParser(response.content.decode(), label).links
                self.assertEqual(len(links), 3 if label == "Thống kê" else 2)
                self.assertEqual(
                    [link["href"] for link in links if link.get("aria-current") == "page"],
                    [reverse(expected)],
                )
        self.assertNotContains(self.client.get(reverse("focus:home")), 'class="section-tabs"')

    def test_public_pages_have_no_header_menu(self):
        self.client.logout()
        for name in ("core:home", "accounts:login", "accounts:register"):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "components/public_layout.html")
                self.assertNotContains(response, 'aria-label="Điều hướng chính"')
                self.assertNotContains(response, 'name="header-menu"')

    def test_avatar_admin_link_requires_staff(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertNotContains(response, reverse("admin:index"))
        self.owner.is_staff = True
        self.owner.save(update_fields=["is_staff"])
        self.assertContains(self.client.get(reverse("accounts:profile")), reverse("admin:index"))

    def test_settings_remain_private_and_busy_events_remain_owned(self):
        self.client.force_login(self.other)
        for name in ("planner:busy_update", "planner:busy_delete"):
            self.assertEqual(self.client.get(reverse(name, args=[self.event.pk])).status_code, 404)
        self.client.logout()
        for name in ("planner:preferences", "planner:busy_list", "notifications:preferences", "integrations:google"):
            path = reverse(name)
            self.assertRedirects(self.client.get(path), f"{reverse('accounts:login')}?next={path}")

    def test_password_done_preserves_legacy_url_and_redirects_with_message(self):
        response = self.client.get(reverse("accounts:password_change_done"), follow=True)
        self.assertRedirects(response, reverse("accounts:profile"))
        self.assertContains(response, "Đổi mật khẩu thành công.")
        response = self.client.get(reverse("accounts:profile"))
        self.assertNotContains(response, "Đổi mật khẩu thành công.")

    def test_week_keeps_original_inheritance_without_settings_layout(self):
        response = self.client.get(reverse("planner:week"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "planner/base.html")
        self.assertTemplateNotUsed(response, "components/settings_layout.html")
        self.assertContains(response, 'aria-label="Chuyển tuần"')
        self.assertContains(response, reverse("planner:plan_generate"))
