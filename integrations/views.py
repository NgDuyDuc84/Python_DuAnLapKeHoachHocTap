import secrets
import time
import uuid
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.debug import sensitive_variables
from django.views.decorators.http import require_POST
from google.auth.exceptions import GoogleAuthError
from oauthlib.oauth2 import OAuth2Error
import requests

from planner.forms import WeekForm

from .google import ERRORS, SyncError, configured, encrypt_credentials, google_identity, oauth_flow, revoke_credentials
from .models import CalendarConnection, CalendarSyncJob
from .services import queue_job, snapshot


SALT = "google-calendar-preview"


@login_required
def home(request):
    connection = CalendarConnection.objects.filter(owner=request.user).first()
    week = timezone.localdate()
    week -= timedelta(days=week.weekday())
    form = WeekForm(request.GET or None, initial={"week": week})
    data = token = None
    rows = []
    if form.is_bound and form.is_valid() and connection and connection.is_connected:
        week = form.cleaned_data["week"]
        data = snapshot(connection, week)
        rows = [{
            "title": payload["summary"],
            "starts_at": parse_datetime(payload["start"]["dateTime"]),
            "ends_at": parse_datetime(payload["end"]["dateTime"]),
        } for payload in data["desired"].values()]
        token = signing.dumps({
            "owner": request.user.pk, "connection": connection.pk,
            "generation": str(connection.generation), "week": week.isoformat(), "hash": data["hash"],
        }, salt=SALT)
    return render(request, "integrations/google.html", {
        "connection": connection, "configured": configured(), "form": form,
        "preview": data, "token": token, "week": week,
        "rows": rows,
        "jobs": CalendarSyncJob.objects.filter(connection__owner=request.user)[:10],
        "error": ERRORS.get(connection.last_error, "") if connection else "",
    })


@login_required
@require_POST
@sensitive_variables()
def connect(request):
    try:
        flow = oauth_flow()
        url, state = flow.authorization_url(access_type="offline", prompt="consent")
    except SyncError as exc:
        messages.error(request, str(exc))
        return redirect("integrations:google")
    request.session["google_oauth"] = {
        "state": state, "verifier": flow.code_verifier,
        "issued": time.time(), "owner": request.user.pk,
    }
    return redirect(url)


@login_required
@sensitive_variables()
def callback(request):
    pending = request.session.pop("google_oauth", None)
    if (
        not pending or pending["owner"] != request.user.pk
        or not 0 <= time.time() - pending["issued"] <= 600
        or not secrets.compare_digest(pending["state"].encode(), request.GET.get("state", "").encode())
    ):
        messages.error(request, "Phiên cấp quyền không hợp lệ hoặc đã hết hạn. Hãy kết nối lại.")
        return redirect("integrations:google")
    if request.GET.get("error") or not request.GET.get("code"):
        messages.error(request, "Chưa được cấp quyền Google. Bạn có thể thử lại khi sẵn sàng.")
        return redirect("integrations:google")
    try:
        flow = oauth_flow(state=pending["state"], code_verifier=pending["verifier"])
        flow.fetch_token(code=request.GET["code"], timeout=15)
        identity = google_identity(flow.credentials)
        with transaction.atomic():
            connection, _ = CalendarConnection.objects.get_or_create(owner=request.user)
            if connection.is_connected and connection.google_sub != identity["sub"]:
                messages.error(request, "Hãy ngắt kết nối hiện tại trước khi đổi tài khoản Google.")
                return redirect("integrations:google")
            if connection.google_sub and connection.google_sub != identity["sub"]:
                connection.calendareventmapping_set.all().delete()
                connection.calendar_id = ""
                connection.calendar_state = CalendarConnection.CalendarState.EMPTY
                connection.last_sync_at = None
            connection.google_sub = identity["sub"]
            if connection.calendar_state == CalendarConnection.CalendarState.CREATING:
                connection.calendar_state = CalendarConnection.CalendarState.UNCERTAIN
            connection.email = identity["email"]
            connection.encrypted_credentials = encrypt_credentials(flow.credentials)
            connection.is_connected = True
            connection.generation = uuid.uuid4()
            connection.last_error = ""
            connection.save()
            connection.calendarsyncjob_set.filter(status__in=["pending", "running"]).update(
                status=CalendarSyncJob.Status.STALE, error="stale", finished_at=timezone.now(), claim_token=None,
            )
        messages.success(request, "Đã kết nối Google. Chọn tuần để xem trước thay đổi.")
    except (SyncError, OAuth2Error, GoogleAuthError, requests.RequestException, ValueError):
        messages.error(request, "Chưa kết nối được Google. Kiểm tra cấu hình và cấp đủ quyền, rồi thử lại.")
    return redirect("integrations:google")


@login_required
@require_POST
def disconnect(request):
    connection = get_object_or_404(CalendarConnection, owner=request.user)
    request.session.pop("google_oauth", None)
    encrypted = connection.encrypted_credentials
    with transaction.atomic():
        CalendarConnection.objects.filter(pk=connection.pk, calendar_state="creating").update(
            calendar_state=CalendarConnection.CalendarState.UNCERTAIN,
        )
        CalendarConnection.objects.filter(pk=connection.pk).update(
            is_connected=False, encrypted_credentials="", generation=uuid.uuid4(), last_error="",
        )
        connection.calendarsyncjob_set.filter(status__in=["pending", "running"]).update(
            status=CalendarSyncJob.Status.STALE, error="stale", finished_at=timezone.now(), claim_token=None,
        )
    revoked = revoke_credentials(encrypted) if encrypted else True
    text = "Đã ngắt kết nối. Lịch và sự kiện đã có trên Google được giữ lại."
    if not revoked:
        text += " Chưa xác nhận thu hồi quyền trên Google; hãy gỡ quyền Nhịp Học trong tài khoản Google."
    messages.success(request, text)
    return redirect("integrations:google")


@login_required
@require_POST
def sync(request):
    connection = get_object_or_404(CalendarConnection, owner=request.user, is_connected=True)
    try:
        preview = signing.loads(request.POST.get("preview", ""), salt=SALT, max_age=600)
        week = date.fromisoformat(preview["week"])
        if (
            preview["owner"] != request.user.pk or preview["connection"] != connection.pk
            or preview["generation"] != str(connection.generation) or week.weekday() != 0
            or snapshot(connection, week)["hash"] != preview["hash"]
        ):
            raise ValueError
    except (signing.BadSignature, ValueError, KeyError, TypeError):
        messages.error(request, ERRORS["stale"])
        return redirect("integrations:google")
    if connection.calendar_state in ("creating", "uncertain") or connection.last_error == "calendar_missing":
        messages.error(request, "Kiểm tra lịch Google và xác nhận tạo lịch đích mới trước khi đồng bộ lại.")
        return redirect("integrations:google")
    job, created = queue_job(connection, week, preview["hash"])
    messages.success(request, "Đã xếp hàng đồng bộ. Worker sẽ xử lý yêu cầu." if created else "Đã có yêu cầu đang chờ hoặc đang chạy. Hãy chờ xử lý xong.")
    return redirect("integrations:job", pk=job.pk) if job else redirect("integrations:google")


@login_required
@require_POST
def reset_calendar(request):
    connection = get_object_or_404(CalendarConnection, owner=request.user, is_connected=True)
    if (
        request.POST.get("confirm") == "checked"
        and (connection.calendar_state == "uncertain" or connection.last_error == "calendar_missing")
        and not connection.calendarsyncjob_set.filter(status__in=["pending", "running"]).exists()
    ):
        with transaction.atomic():
            connection.calendareventmapping_set.all().delete()
            connection.calendar_id = ""
            connection.calendar_state = CalendarConnection.CalendarState.EMPTY
            connection.generation = uuid.uuid4()
            connection.last_error = ""
            connection.save()
        messages.success(request, "Đã cho phép tạo lịch mới ở lần đồng bộ tiếp theo. Lịch cũ trên Google được giữ lại.")
    else:
        messages.error(request, "Cần kiểm tra Google, đánh dấu xác nhận và chờ worker kết thúc.")
    return redirect("integrations:google")


@login_required
def job_detail(request, pk):
    job = get_object_or_404(CalendarSyncJob, pk=pk, connection__owner=request.user)
    return render(request, "integrations/job.html", {"job": job, "error": ERRORS.get(job.error, "")})
