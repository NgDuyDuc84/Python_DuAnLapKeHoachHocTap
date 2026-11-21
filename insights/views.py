import json
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
from .provider import ERRORS, NON_COUNTING_ERRORS, InsightError, configured
from .services import generate_report


SALT = "insight-data-preview"


def sections(result, labels):
    return [{"title": title, "points": [{
        "text": point["text"],
        "evidence": [{"ref": ref, "label": labels[ref]} for ref in point["evidence"]],
    } for point in points]} for title, points in (
        ("Tóm tắt", [result["summary"]]), ("Thói quen học", result["habits"]),
        ("Gợi ý phân bổ", result["allocation"]), ("Giải thích cảnh báo", result["warnings"]),
    )]


def home_context(user, *, form=None):
    snapshot = build_snapshot(user)
    payload = snapshot["payload"]
    token = signing.dumps({
        "owner": user.pk, "as_of": payload["as_of"], "hash": fingerprint(snapshot), "request_key": str(uuid.uuid4()),
    }, salt=SALT)
    if form is not None:
        form.data = form.data.copy()
        form.data["preview"] = token
    tasks = [{**row, "title": snapshot["labels"][row["ref"]]} for row in payload["tasks"]]
    reports = InsightReport.objects.filter(owner=user)
    used_today = reports.filter(created_at__date=timezone.localdate()).exclude(
        status="failed", error__in=NON_COUNTING_ERRORS,
    ).count()
    return {
        "snapshot": snapshot, "totals": payload["facts"]["H01"], "tasks": tasks,
        "payload_json": json.dumps(payload, ensure_ascii=False, indent=2),
        "sections": sections(baseline_report(snapshot), snapshot["labels"]),
        "form": form if form is not None else AnalyzeForm(initial={"preview": token}),
        "configured": configured(), "remaining_requests": max(0, 5 - used_today),
        "reports": reports[:10],
    }


@login_required
def home(request):
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
    as_of = parse_datetime(report.snapshot["payload"]["as_of"])
    changed = fingerprint(build_snapshot(request.user, now=as_of)) != report.input_hash
    return render(request, "insights/report.html", {
        "report": report, "as_of": as_of, "changed": changed, "error": ERRORS.get(report.error, ""),
        "counts_toward_limit": report.error not in NON_COUNTING_ERRORS,
        "sections": sections(report.result, report.snapshot["labels"]) if report.status == "success" else [],
        "payload_json": json.dumps(report.snapshot["payload"], ensure_ascii=False, indent=2),
    })
