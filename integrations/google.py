import json
from urllib.parse import quote

import requests
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow


CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.app.created"
SCOPES = [CALENDAR_SCOPE, "openid", "https://www.googleapis.com/auth/userinfo.email"]
ERRORS = {
    "configuration": "Chưa cấu hình Google OAuth hoặc khóa mã hóa hợp lệ.",
    "credentials": "Không đọc được thông tin cấp quyền. Hãy kết nối lại Google.",
    "authorization": "Quyền Google đã hết hạn hoặc bị từ chối. Hãy kết nối lại.",
    "network": "Không liên lạc được Google. Bạn có thể xem trước và đồng bộ lại.",
    "provider": "Google chưa xử lý được yêu cầu. Hãy kiểm tra quyền hoặc hạn mức rồi thử lại.",
    "calendar_missing": "Không tìm thấy lịch đích. Kiểm tra Google trước khi cho tạo lịch mới.",
    "calendar_uncertain": "Chưa xác nhận Google đã tạo lịch hay chưa. Kiểm tra Google trước khi cho tạo lịch mới.",
    "event_owner": "Sự kiện không còn dấu nhận diện của ứng dụng; đã dừng để tránh sửa nhầm.",
    "stale": "Dữ liệu hoặc kết nối đã thay đổi. Hãy xem trước và đồng bộ lại.",
}


class SyncError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(ERRORS[code])


def cipher():
    try:
        return Fernet(settings.GOOGLE_TOKEN_ENCRYPTION_KEY.encode())
    except (ValueError, TypeError, AttributeError):
        raise SyncError("configuration") from None


def configured():
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        return False
    try:
        cipher()
    except SyncError:
        return False
    return True


def encrypt_credentials(credentials):
    return cipher().encrypt(credentials.to_json().encode()).decode()


def decrypt_credentials(value):
    try:
        info = json.loads(cipher().decrypt(value.encode()))
        info.update(client_id=settings.GOOGLE_CLIENT_ID, client_secret=settings.GOOGLE_CLIENT_SECRET)
        return Credentials.from_authorized_user_info(info, scopes=SCOPES)
    except (InvalidToken, ValueError, TypeError, KeyError):
        raise SyncError("credentials") from None


def oauth_flow(**kwargs):
    if not configured():
        raise SyncError("configuration")
    return Flow.from_client_config({"web": {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }}, scopes=SCOPES, redirect_uri=settings.GOOGLE_REDIRECT_URI, **kwargs)


def google_identity(credentials):
    try:
        with AuthorizedSession(credentials, refresh_timeout=15) as session:
            response = session.get("https://openidconnect.googleapis.com/v1/userinfo", timeout=15)
            response.raise_for_status()
            identity = response.json()
        if not identity.get("sub") or not identity.get("email") or not identity.get("email_verified"):
            raise SyncError("authorization")
        granted = credentials.granted_scopes
        if isinstance(granted, str):
            granted = granted.split()
        if not credentials.refresh_token or CALENDAR_SCOPE not in (granted or []):
            raise SyncError("authorization")
        return identity
    except (requests.RequestException, GoogleAuthError, ValueError):
        raise SyncError("authorization") from None


def revoke_credentials(encrypted):
    try:
        credentials = decrypt_credentials(encrypted)
        response = requests.post("https://oauth2.googleapis.com/revoke", data={
            "token": credentials.refresh_token,
        }, timeout=15)
        return response.status_code in (200, 400)
    except (SyncError, requests.RequestException):
        return False


class GoogleCalendarClient:
    def __init__(self, connection):
        self.connection = connection
        self.credentials = decrypt_credentials(connection.encrypted_credentials)
        self.session = AuthorizedSession(self.credentials, refresh_timeout=15)

    def close(self):
        self.session.close()

    def request(self, method, path, **kwargs):
        from .models import CalendarConnection

        try:
            response = self.session.request(
                method, "https://www.googleapis.com/calendar/v3/" + path,
                timeout=15, **kwargs,
            )
        except GoogleAuthError:
            raise SyncError("authorization") from None
        except requests.RequestException:
            raise SyncError("network") from None
        finally:
            CalendarConnection.objects.filter(
                pk=self.connection.pk, is_connected=True, generation=self.connection.generation,
            ).update(encrypted_credentials=encrypt_credentials(self.credentials))
        if response.status_code in (404, 410):
            return None
        if response.status_code == 409:
            return {"conflict": True}
        if response.status_code == 401:
            raise SyncError("authorization")
        if not 200 <= response.status_code < 300:
            raise SyncError("provider")
        if response.status_code == 204 or not response.content:
            return {}
        try:
            return response.json()
        except ValueError:
            raise SyncError("provider") from None

    def calendar(self, calendar_id):
        return self.request("GET", "calendars/" + quote(calendar_id, safe=""))

    def create_calendar(self):
        return self.request("POST", "calendars", json={
            "summary": "Nhịp Học", "timeZone": settings.TIME_ZONE,
            "description": "Buổi học đồng bộ một chiều từ ứng dụng Nhịp Học.",
        })

    def event(self, calendar_id, event_id):
        return self.request("GET", self.event_path(calendar_id, event_id))

    def upsert(self, calendar_id, event_id, payload, *, exists):
        return self.request(
            "PATCH" if exists else "POST",
            self.event_path(calendar_id, event_id if exists else ""),
            json=payload if exists else {"id": event_id, **payload},
            params={"sendUpdates": "none"},
        )

    def delete(self, calendar_id, event_id):
        return self.request("DELETE", self.event_path(calendar_id, event_id), params={"sendUpdates": "none"})

    @staticmethod
    def event_path(calendar_id, event_id):
        path = "calendars/" + quote(calendar_id, safe="") + "/events"
        return path + ("/" + quote(event_id, safe="") if event_id else "")
