from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

User = get_user_model()


class AccountFlowTests(TestCase):
    password = "River!Study-2026-Maple"
    new_password = "Willow!Plan-2026-Cloud"

    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create_user(
            username="student_a", email="student_a@example.test", password=cls.password
        )
        cls.other = User.objects.create_user(
            username="student_b", email="student_b@example.test", password=cls.password
        )
        cls.admin = User.objects.create_superuser(
            username="test_admin", email="admin@example.test", password=cls.password
        )

    def registration_data(self, **overrides):
        data = {
            "username": "new_learner",
            "email": "new_learner@example.test",
            "password1": self.password,
            "password2": self.password,
        }
        data.update(overrides)
        return data

    def test_registration_hashes_password_and_ignores_forged_admin_flags(self):
        response = self.client.post(
            reverse("accounts:register"),
            self.registration_data(is_staff="on", is_superuser="on"),
        )
        self.assertRedirects(response, reverse("accounts:login"))
        user = User.objects.get(username="new_learner")
        self.assertTrue(user.check_password(self.password))
        self.assertNotEqual(user.password, self.password)
        self.assertEqual(user.email, "new_learner@example.test")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_invalid_registration_does_not_create_accounts(self):
        cases = [
            ({"username": self.student.username}, "username"),
            ({"password2": self.new_password}, "password2"),
            ({"password1": "123", "password2": "123"}, "password2"),
            ({"email": "invalid-email"}, "email"),
            ({"email": ""}, "email"),
        ]
        for changes, error_field in cases:
            with self.subTest(changes=changes):
                response = self.client.post(
                    reverse("accounts:register"), self.registration_data(**changes)
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn(error_field, response.context["form"].errors)
                self.assertEqual(User.objects.count(), 3)

    def test_authenticated_user_cannot_register_another_account(self):
        self.client.force_login(self.student)
        for name in ("accounts:register", "accounts:login"):
            with self.subTest(name=name):
                self.assertRedirects(
                    self.client.get(reverse(name)), reverse("core:home")
                )
        response = self.client.post(
            reverse("accounts:register"), self.registration_data()
        )
        self.assertRedirects(response, reverse("core:home"))
        self.assertEqual(User.objects.count(), 3)

    def test_login_opens_dashboard_and_profile_is_accessible(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": self.student.username, "password": self.password},
        )
        self.assertRedirects(response, reverse("core:home"))
        response = self.client.get(reverse("accounts:profile"))
        self.assertContains(response, self.student.email)
        self.assertContains(response, reverse("accounts:logout"))
        self.assertNotContains(response, "Mở trang quản trị")

    def test_wrong_password_and_disabled_account_cannot_login(self):
        self.other.is_active = False
        self.other.save(update_fields=["is_active"])
        for username, password in (
            (self.student.username, "wrong-password"),
            (self.other.username, self.password),
        ):
            with self.subTest(username=username):
                response = self.client.post(
                    reverse("accounts:login"),
                    {"username": username, "password": password},
                )
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].non_field_errors())
                self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_rejects_external_next_urls(self):
        for target in ("https://evil.example/", "//evil.example/"):
            with self.subTest(target=target):
                client = Client()
                response = client.post(
                    reverse("accounts:login"),
                    {
                        "username": self.student.username,
                        "password": self.password,
                        "next": target,
                    },
                )
                self.assertRedirects(response, reverse("core:home"))

    def test_login_preserves_safe_next_url(self):
        target = reverse("accounts:password_change")
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": self.student.username,
                "password": self.password,
                "next": target,
            },
        )
        self.assertRedirects(response, target)

    def test_anonymous_users_are_redirected_from_private_pages(self):
        for name in (
            "accounts:profile",
            "accounts:password_change",
            "accounts:password_change_done",
        ):
            with self.subTest(name=name):
                path = reverse(name)
                self.assertRedirects(
                    self.client.get(path),
                    f"{reverse('accounts:login')}?next={path}",
                )

    def test_profile_cannot_be_switched_to_another_user_by_query_parameters(self):
        self.client.force_login(self.student)
        response = self.client.get(
            reverse("accounts:profile"),
            {"user_id": self.other.pk, "username": self.other.username},
        )
        self.assertContains(response, self.student.email)
        self.assertNotContains(response, self.other.email)
        self.assertNotContains(response, self.student.password)

    def test_logout_requires_post_and_clears_the_session(self):
        self.client.force_login(self.student)
        self.assertEqual(
            self.client.get(reverse("accounts:logout")).status_code, 405
        )
        self.assertIn("_auth_user_id", self.client.session)
        self.assertRedirects(
            self.client.post(reverse("accounts:logout")), reverse("core:home")
        )
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(
            self.client.get(reverse("accounts:profile")).status_code, 302
        )

    def test_auth_posts_require_csrf_and_valid_token_allows_login(self):
        strict_client = Client(enforce_csrf_checks=True)
        strict_client.force_login(self.student)
        for name in (
            "accounts:register",
            "accounts:login",
            "accounts:logout",
            "accounts:password_change",
        ):
            with self.subTest(name=name):
                self.assertEqual(
                    strict_client.post(reverse(name), {}).status_code, 403
                )
        strict_client.logout()
        strict_client.get(reverse("accounts:login"))
        response = strict_client.post(
            reverse("accounts:login"),
            {
                "username": self.student.username,
                "password": self.password,
                "csrfmiddlewaretoken": strict_client.cookies["csrftoken"].value,
            },
        )
        self.assertRedirects(response, reverse("core:home"))

    def test_password_change_keeps_current_session_and_revokes_other_session(self):
        self.client.login(username=self.student.username, password=self.password)
        other_session = Client()
        other_session.login(username=self.student.username, password=self.password)
        response = self.client.post(
            reverse("accounts:password_change"),
            {
                "old_password": self.password,
                "new_password1": self.new_password,
                "new_password2": self.new_password,
                "user_id": self.other.pk,
                "is_superuser": "on",
            },
        )
        self.assertRedirects(
            response, reverse("accounts:password_change_done"),
            fetch_redirect_response=False,
        )
        response = self.client.get(response.url, follow=True)
        self.assertRedirects(response, reverse("accounts:profile"))
        self.assertContains(response, "Đổi mật khẩu thành công.")
        self.assertEqual(
            self.client.get(reverse("accounts:profile")).status_code, 200
        )
        self.assertEqual(
            other_session.get(reverse("accounts:profile")).status_code, 302
        )
        self.student.refresh_from_db()
        self.other.refresh_from_db()
        self.assertTrue(self.student.check_password(self.new_password))
        self.assertFalse(self.student.is_superuser)
        self.assertTrue(self.other.check_password(self.password))
        self.client.post(reverse("accounts:logout"))
        self.client.post(
            reverse("accounts:login"),
            {"username": self.student.username, "password": self.password},
        )
        self.assertNotIn("_auth_user_id", self.client.session)
        response = self.client.post(
            reverse("accounts:login"),
            {"username": self.student.username, "password": self.new_password},
        )
        self.assertRedirects(response, reverse("core:home"))

    def test_invalid_password_change_preserves_existing_password(self):
        self.client.force_login(self.student)
        for changes, error_field in (
            ({"old_password": "wrong"}, "old_password"),
            ({"new_password2": self.password}, "new_password2"),
            ({"new_password1": "123", "new_password2": "123"}, "new_password2"),
        ):
            with self.subTest(changes=changes):
                data = {
                    "old_password": self.password,
                    "new_password1": self.new_password,
                    "new_password2": self.new_password,
                }
                data.update(changes)
                response = self.client.post(reverse("accounts:password_change"), data)
                self.assertEqual(response.status_code, 200)
                self.assertIn(error_field, response.context["form"].errors)
                self.student.refresh_from_db()
                self.assertTrue(self.student.check_password(self.password))

    def test_regular_user_cannot_read_admin_users_or_escalate_privileges(self):
        self.client.force_login(self.student)
        for path, method, data in (
            (reverse("admin:auth_user_changelist"), self.client.get, {}),
            (
                reverse("admin:auth_user_change", args=[self.student.pk]),
                self.client.post,
                {"is_staff": "on", "is_superuser": "on"},
            ),
        ):
            with self.subTest(path=path):
                response = method(path, data)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse("admin:login")))
        self.student.refresh_from_db()
        self.assertFalse(self.student.is_staff)
        self.assertFalse(self.student.is_superuser)

    def test_staff_without_user_permissions_cannot_manage_users(self):
        self.other.is_staff = True
        self.other.save(update_fields=["is_staff"])
        self.client.force_login(self.other)
        self.assertEqual(
            self.client.get(reverse("admin:auth_user_changelist")).status_code, 403
        )

    def test_admin_can_disable_and_reenable_user_from_admin_form(self):
        self.client.force_login(self.admin)
        self.assertEqual(
            self.client.get(reverse("admin:auth_user_changelist")).status_code, 200
        )
        user_session = Client()
        user_session.force_login(self.student)
        joined = timezone.localtime(self.student.date_joined)
        for active in (False, True):
            with self.subTest(active=active):
                data = {
                    "username": self.student.username,
                    "email": self.student.email,
                    "date_joined_0": joined.strftime("%Y-%m-%d"),
                    "date_joined_1": joined.strftime("%H:%M:%S"),
                }
                if active:
                    data["is_active"] = "on"
                response = self.client.post(
                    reverse("admin:auth_user_change", args=[self.student.pk]), data
                )
                self.assertRedirects(response, reverse("admin:auth_user_changelist"))
                self.student.refresh_from_db()
                self.assertEqual(self.student.is_active, active)
                if not active:
                    self.assertEqual(
                        user_session.get(reverse("accounts:profile")).status_code, 302
                    )
                self.assertEqual(
                    user_session.login(
                        username=self.student.username, password=self.password
                    ),
                    active,
                )
