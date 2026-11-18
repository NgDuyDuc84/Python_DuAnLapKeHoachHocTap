from html.parser import HTMLParser

from django.test import TestCase
from django.urls import reverse


class AuthMarkup(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.headings = []
        self.inputs = {}
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("h1", "h2"):
            self.headings.append(tag)
        if tag == "input" and attrs.get("type") != "hidden":
            self.inputs[attrs["name"]] = attrs


class AuthLayoutTests(TestCase):
    def test_public_pages_share_split_layout_and_keep_semantic_form_fields(self):
        for name, mode, title, fields, target in (
            ("core:home", "login", "Đăng nhập", {"username": "username", "password": "current-password"}, "accounts:register"),
            ("accounts:login", "login", "Đăng nhập", {"username": "username", "password": "current-password"}, "accounts:register"),
            ("accounts:register", "register", "Tạo tài khoản", {"username": "username", "email": "email", "password1": "new-password", "password2": "new-password"}, "accounts:login"),
        ):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "accounts/auth_split.html")
                self.assertContains(response, f'auth-split--{mode}')
                self.assertContains(response, f'<title>{title} · Nhịp Học</title>', html=True)
                self.assertContains(response, f'href="{reverse(target)}"')
                self.assertContains(response, f'action="{reverse("accounts:" + mode)}"')
                self.assertContains(response, 'name="csrfmiddlewaretoken"')
                markup = response.content.decode()
                parsed = AuthMarkup(markup)
                self.assertEqual(parsed.headings, ["h2", "h1"])
                self.assertEqual(set(parsed.inputs), set(fields))
                self.assertIn("autofocus", parsed.inputs["username"])
                for field, autocomplete in fields.items():
                    self.assertEqual(parsed.inputs[field]["autocomplete"], autocomplete)
                self.assertLess(markup.index('class="auth-info"'), markup.index('class="auth-panel"'))
                self.assertNotIn('class="field-help"', markup)
                self.assertNotIn('_helptext', markup)
                self.assertNotIn('class="errorlist"', markup)
                self.assertNotIn("Học có kế hoạch.", markup)
                self.assertContains(response, "images/auth/book.png" if mode == "register" else "images/auth/calendar.png")
                self.assertNotIn("<script", markup)
                self.assertNotIn("<nav", markup)
                self.assertContains(response, '© Nhịp Học', count=1)

    def test_invalid_login_preserves_next_and_shows_general_error_summary(self):
        response = self.client.post(reverse("accounts:login"), {
            "username": "unknown", "password": "wrong", "next": reverse("planner:week"),
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="form-errors" role="alert"')
        self.assertContains(response, 'name="next" value="/planner/"')
        self.assertContains(response, 'value="unknown"')
        for error in response.context["form"].non_field_errors():
            self.assertContains(response, error)

    def test_invalid_registration_keeps_field_errors_linked_to_inputs(self):
        response = self.client.post(reverse("accounts:register"), {
            "username": "new_student", "email": "invalid", "password1": "Study!Maple-2026", "password2": "mismatch",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'auth-split--register')
        form = response.context["form"]
        self.assertIn("email", form.errors)
        self.assertIn("password2", form.errors)
        self.assertContains(response, 'aria-invalid="true"', count=2)
        for field in ("email", "password2"):
            self.assertContains(response, f'id="id_{field}_error"')
