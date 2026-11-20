import base64
import smtplib
from email import policy
from email.parser import BytesParser
from unittest.mock import patch

import requests
from django.core.mail import EmailMessage, send_mail
from django.test import SimpleTestCase, override_settings
from google.auth.exceptions import RefreshError


@override_settings(
    EMAIL_BACKEND="notifications.gmail_backend.EmailBackend",
    GOOGLE_CLIENT_ID="test-client", GOOGLE_CLIENT_SECRET="test-secret",
    GMAIL_REFRESH_TOKEN="test-refresh-token", EMAIL_TIMEOUT=10,
    DEFAULT_FROM_EMAIL="Nhịp Học <sender@example.test>",
)
class GmailBackendTests(SimpleTestCase):
    def setUp(self):
        self.credentials_patch = patch("notifications.gmail_backend.Credentials")
        self.credentials = self.credentials_patch.start()
        self.addCleanup(self.credentials_patch.stop)
        self.credentials.return_value.token = "test-access-token"
        self.session_patch = patch("notifications.gmail_backend.requests.Session")
        self.session = self.session_patch.start().return_value.__enter__.return_value
        self.addCleanup(self.session_patch.stop)
        self.session.post.return_value.status_code = 200
        self.session.post.return_value.json.return_value = {"id": "gmail-message-id"}

    def send(self, **kwargs):
        return send_mail("Nhắc học", "Sắp đến giờ học.", None, ["student@example.test"], **kwargs)

    def test_sends_unicode_mime_over_https_with_oauth_and_no_secret_in_body(self):
        self.assertEqual(self.send(), 1)
        args, kwargs = self.session.post.call_args
        self.assertEqual(args, ("https://gmail.googleapis.com/gmail/v1/users/me/messages/send",))
        self.assertEqual(kwargs["headers"], {"Authorization": "Bearer test-access-token"})
        self.assertEqual(kwargs["timeout"], 10)
        self.assertFalse(kwargs["allow_redirects"])
        message = BytesParser(policy=policy.default).parsebytes(base64.urlsafe_b64decode(kwargs["json"]["raw"]))
        self.assertEqual(str(message["Subject"]), "Nhắc học")
        self.assertIn("sender@example.test", str(message["From"]))
        self.assertEqual(str(message["To"]), "student@example.test")
        self.assertIn("Sắp đến giờ học.", message.get_content())
        self.assertNotIn("test-refresh-token", str(kwargs))
        self.credentials.return_value.refresh.assert_called_once()

    @override_settings(GMAIL_REFRESH_TOKEN="")
    def test_missing_config_fails_before_network(self):
        with self.assertRaises(smtplib.SMTPAuthenticationError):
            self.send()
        self.session.post.assert_not_called()
        self.credentials.assert_not_called()

    def test_invalid_refresh_token_is_sanitized_and_does_not_send(self):
        self.credentials.return_value.refresh.side_effect = RefreshError("PRIVATE SECRET")
        with self.assertRaises(smtplib.SMTPAuthenticationError) as error:
            self.send()
        self.assertNotIn("PRIVATE", str(error.exception))
        self.session.post.assert_not_called()

    def test_rejected_request_can_follow_existing_worker_retry_policy(self):
        for code in (400, 401, 403, 404, 429):
            self.session.post.return_value.status_code = code
            with self.subTest(code=code), self.assertRaises(smtplib.SMTPResponseException):
                self.send()

    def test_timeout_server_error_redirect_and_missing_id_are_uncertain_without_retry(self):
        for code in (302, 500, 503):
            self.session.post.return_value.status_code = code
            self.session.post.reset_mock()
            with self.subTest(code=code), self.assertRaises(smtplib.SMTPException) as error:
                self.send()
            self.assertNotIsInstance(error.exception, smtplib.SMTPResponseException)
            self.session.post.assert_called_once()
        self.session.post.return_value.status_code = 200
        self.session.post.return_value.json.return_value = {}
        with self.assertRaises(smtplib.SMTPException):
            self.send()
        self.session.post.side_effect = requests.Timeout("PRIVATE SECRET")
        with self.assertRaises(smtplib.SMTPException) as error:
            self.send()
        self.assertNotIn("PRIVATE", str(error.exception))

    def test_fail_silently_returns_zero(self):
        self.session.post.side_effect = requests.Timeout()
        self.assertEqual(self.send(fail_silently=True), 0)

    def test_no_recipients_does_not_send(self):
        self.assertEqual(EmailMessage("Subject", "Body", to=[]).send(), 0)
        self.session.post.assert_not_called()
