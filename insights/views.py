import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.db import OperationalError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST

from .data import baseline_report, build_snapshot, fingerprint
from .forms import AnalyzeForm
from .models import InsightReport
from .presentation import latest_context, period_text, preview_context, request_context, sections, snapshot_time
from .provider import ERRORS, NON_COUNTING_ERRORS, InsightError
from .services import generate_report


SALT = "insight-data-preview"


def signed_request_context(user, *, form=None):
    snapshot = build_snapshot(user)
    payload = snapshot["payload"]
    token = signing.dumps({
        "owner": user.pk, "as_of": payload["as_of"], "hash": fingerprint(snapshot), "request_key": str(uuid.uuid4()),
    }, salt=SALT)
    if form is not None:
        form.data = form.data.copy()
        form.data["preview"] = token
    else:
        form = AnalyzeForm(initial={"preview": token})
    return {**request_context(user, form), **preview_context(snapshot), "snapshot": snapshot}


def home_context(user, *, form=None):
    context = signed_request_context(user, form=form)
    snapshot = context["snapshot"]
    payload = snapshot["payload"]
    latest = latest_context(user)
    reports = InsightReport.objects.filter(owner=user)
    if latest["latest_insight"]:
        reports = reports.exclude(pk=latest["latest_insight"].pk)
    return {
        **context, **latest, "totals": payload["facts"]["H01"], "current_period": period_text(payload),
        "tasks": [{**row, "title": snapshot["labels"][row["ref"]]} for row in payload["tasks"]],
        "sections": sections(baseline_report(snapshot), snapshot),
        "reports": [{"report": report, "period": period_text(report.snapshot.get("payload", {}))}
                    for report in reports.only("created_at", "status", "snapshot")[:10]],
    }


@login_required
def home(request):
    if request.GET.get("panel") == "request":
        response = render(request, "insights/request_controls.html", signed_request_context(request.user))
        response["Cache-Control"] = "private, no-store"
        return response
    return render(request, "insights/home.html", home_context(request.user))


@login_required
@require_POST
def generate(request):
    form = AnalyzeForm(request.POST)
    if not form.is_valid():
        return render(request, "insights/home.html", home_context(request.user, form=form), status=400)
    try:
        preview = signing.loads(form.cleaned_data["preview"], salt=SALT, max_age=600)
        as_of = parse_datetime(preview["as_of"])
        key = uuid.UUID(preview["request_key"])
        if preview["owner"] != request.user.pk or as_of is None or timezone.is_naive(as_of):
            raise ValueError
        previous = InsightReport.objects.filter(owner=request.user, request_key=key).first()
        if previous:
            return redirect("insights:report", pk=previous.pk)
        snapshot = build_snapshot(request.user, now=as_of)
        if fingerprint(snapshot) != preview["hash"]:
            raise ValueError
    except (signing.BadSignature, ValueError, TypeError, KeyError):
        messages.error(request, "Dữ liệu xem trước đã đổi, hết hạn hoặc không hợp lệ. Hãy kiểm tra bản mới rồi xác nhận lại.")
        return redirect("insights:home")
    try:
        report = generate_report(request.user, snapshot, key)
    except InsightError as exc:
        messages.error(request, str(exc))
        return redirect("insights:home")
    except OperationalError as exc:
        if "locked" not in str(exc).lower():
            raise
        messages.error(request, "Database đang bận. Hãy tải lại lịch sử trước khi yêu cầu phân tích mới.")
        return redirect("insights:home")
    return redirect("insights:report", pk=report.pk)


@login_required
def report_detail(request, pk):
    report = get_object_or_404(InsightReport, pk=pk, owner=request.user)
    payload = report.snapshot.get("payload", {})
    as_of = snapshot_time(payload)
    changed = as_of and timezone.is_aware(as_of) and fingerprint(build_snapshot(request.user, now=as_of)) != report.input_hash
    return render(request, "insights/report.html", {
        "report": report, "as_of": as_of, "changed": changed, "error": ERRORS.get(report.error, ""),
        "counts_toward_limit": report.error not in NON_COUNTING_ERRORS,
        "sections": sections(report.result, report.snapshot) if report.status == "success" else [],
        "report_period": period_text(payload),
        **(preview_context(report.snapshot) if payload else {}),
    })
