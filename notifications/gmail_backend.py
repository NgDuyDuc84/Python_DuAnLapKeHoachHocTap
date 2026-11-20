"""Django mail backend using Gmail's HTTPS API instead of SMTP."""
import base64
import smtplib
from functools import partial

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


class EmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        sent = 0
        try:
            if not all((settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET, settings.GMAIL_REFRESH_TOKEN)):
                raise smtplib.SMTPAuthenticationError(535, "Chưa cấu hình Gmail API OAuth.")
            with requests.Session() as session:
                credentials = Credentials(
                    token=None, refresh_token=settings.GMAIL_REFRESH_TOKEN,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=settings.GOOGLE_CLIENT_ID, client_secret=settings.GOOGLE_CLIENT_SECRET,
                )
                try:
                    credentials.refresh(partial(Request(session=session), timeout=settings.EMAIL_TIMEOUT))
                except GoogleAuthError:
                    raise smtplib.SMTPAuthenticationError(535, "Quyền gửi Gmail hết hạn hoặc chưa hợp lệ.") from None
                for message in email_messages:
                    if not message.recipients():
                        continue
                    mime = message.message()
                    # Gmail sends to the MIME headers, including blind-copy recipients.
                    if message.bcc:
                        mime["Bcc"] = ", ".join(message.bcc)
                    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode("ascii")
                    try:
                        response = session.post(
                            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                            headers={"Authorization": "Bearer " + credentials.token},
                            json={"raw": raw}, timeout=settings.EMAIL_TIMEOUT, allow_redirects=False,
                        )
                    except requests.RequestException:
                        # Delivery may have happened: let the reminder worker mark it uncertain.
                        raise smtplib.SMTPException("Chưa xác nhận kết quả gửi Gmail.") from None
                    if response.status_code in (400, 401, 403, 404, 429):
                        raise smtplib.SMTPResponseException(response.status_code, "Gmail từ chối yêu cầu gửi.")
                    if not 200 <= response.status_code < 300:
                        raise smtplib.SMTPException("Chưa xác nhận kết quả gửi Gmail.")
                    try:
                        delivered = bool(response.json().get("id"))
                    except (ValueError, AttributeError):
                        delivered = False
                    if not delivered:
                        raise smtplib.SMTPException("Chưa xác nhận kết quả gửi Gmail.")
                    sent += 1
        except smtplib.SMTPException:
            if not self.fail_silently:
                raise
        return sent
