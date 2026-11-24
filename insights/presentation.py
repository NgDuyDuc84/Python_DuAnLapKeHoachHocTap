"""Display values for signed previews and stored reports. Keep the provider payload intact."""
import json
import re
from datetime import date

from django.db.models import Subquery
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from focus.models import StudyLog
from planner.models import DAY_CHOICES
from studies.models import Task

from .forms import AnalyzeForm
from .models import InsightReport
from .provider import NON_COUNTING_ERRORS, configured


FIELD_LABELS = {
    "as_of": "Thời điểm lấy dữ liệu", "timezone": "Múi giờ", "period": "Kỳ nhật ký",
    "start": "Bắt đầu", "end": "Kết thúc", "facts": "Số liệu", "tasks": "Công việc",
    "warnings": "Cảnh báo", "scope": "Phạm vi", "minutes": "Phút học", "entries": "Số bản ghi",
    "study_days": "Ngày học", "daily_average": "Trung bình phút/ngày",
    "previous_7_minutes": "Phút trong 7 ngày trước", "recent_7_minutes": "Phút trong 7 ngày gần nhất",
    "date": "Ngày", "source": "Nguồn ghi nhận", "subjects": "Môn học",
    "omitted_subjects": "Số môn ngoài phạm vi", "unrecorded_sessions": "Buổi chưa ghi nhận",
    "max_daily_minutes": "Số phút học tối đa mỗi ngày", "session_minutes": "Phút mỗi buổi",
    "break_minutes": "Phút nghỉ", "capacity_minutes": "Phút còn trống", "ref": "Tham chiếu",
    "subject_ref": "Môn học", "task_ref": "Công việc", "deadline": "Hạn hoàn thành",
    "priority": "Ưu tiên", "remaining_minutes": "Phút còn lại", "can_split": "Có thể chia buổi",
    "reserved_future_minutes": "Phút đã xếp trong tương lai", "proposed_week_minutes": "Phút đề xuất trong tuần",
    "unallocated_week_minutes": "Phút chưa xếp", "reason": "Lý do", "kind": "Loại cảnh báo",
    "missing_minutes": "Phút còn thiếu", "starts_at": "Bắt đầu", "reasons": "Lý do",
    "unfinished_tasks": "Việc chưa hoàn thành", "included_tasks": "Việc trong phân tích",
    "total_warnings": "Tổng số cảnh báo", "included_warnings": "Cảnh báo trong phân tích",
}
VALUE_LABELS = {
    "source": dict(StudyLog.Source.choices),
    "priority": dict(Task.Priority.choices),
    "kind": {"overdue": "Quá hạn", "missing_schedule": "Chưa đủ lịch trước hạn",
             "session_conflict": "Buổi học đang xung đột"},
}
REF = re.compile(r"\b[HLCVM]\d{2,}\b")


def snapshot_time(payload):
    stamp = payload.get("as_of")
    try:
        return parse_datetime(stamp) if stamp else None
    except (TypeError, ValueError):
        return None


def period_text(payload):
    period = payload.get("period") or {}
    try:
        start, end = (date.fromisoformat(period[key]) for key in ("start", "end"))
    except (ValueError, KeyError, TypeError):
        return ""
    return f"{start:%d/%m/%Y} – {end:%d/%m/%Y}"


def reference_names(snapshot, *, anonymous=False):
    names = dict(snapshot.get("labels", {}))
    if anonymous:
        types = {"V": "Công việc", "M": "Môn", "C": "Cảnh báo"}
        for ref in names:
            if ref[:1] in types and ref[1:].isdigit():
                names[ref] = f"{types[ref[0]]} {int(ref[1:])}"
    return names


def readable(value, names, field=None):
    if field == "study_days" and isinstance(value, list):
        return [dict(DAY_CHOICES).get(day, day) for day in value]
    if field in VALUE_LABELS:
        return VALUE_LABELS[field].get(value, value)
    if isinstance(value, dict):
        return {names.get(key, FIELD_LABELS.get(key, key)): readable(v, names, key) for key, v in value.items()}
    if isinstance(value, list):
        return [readable(v, names) for v in value]
    if isinstance(value, str):
        return REF.sub(lambda m: names.get(m[0], "căn cứ chưa lưu nhãn"), value)
    return value


def preview_context(snapshot):
    payload = snapshot["payload"]
    return {
        "preview_display": json.dumps(readable(payload, reference_names(snapshot, anonymous=True)),
                                      ensure_ascii=False, indent=2),
        "payload_json": json.dumps(payload, ensure_ascii=False, indent=2),
    }


def display_value(value):
    if isinstance(value, list):
        return " · ".join(display_value(item) for item in value) or "—"
    if isinstance(value, dict):
        return ", ".join(f"{key}: {display_value(item)}" for key, item in value.items())
    if isinstance(value, bool):
        return "Có" if value else "Không"
    return str(value) if value != "" else "—"


def sections(result, snapshot):
    labels = reference_names(snapshot)
    payload = snapshot.get("payload", {})
    sources = dict(payload.get("facts", {}))
    for row in [*payload.get("tasks", []), *payload.get("warnings", [])]:
        sources[row["ref"]] = row

    def present(point):
        evidence = []
        overdue = False
        for ref in point.get("evidence", []):
            if ref not in labels or ref not in sources:
                continue
            source = sources[ref]
            overdue |= isinstance(source, dict) and source.get("kind") == "overdue"
            rows = source if isinstance(source, list) else [source]
            evidence.append({"label": labels[ref], "rows": [
                {field: display_value(value) for field, value in readable(row, labels).items()}
                for row in rows
            ]})
        return {"text": readable(point["text"], labels), "evidence": evidence, "overdue": overdue}

    groups = (("Tóm tắt", [result["summary"]] if result.get("summary") else []),
              ("Thói quen học", result.get("habits", [])), ("Gợi ý phân bổ", result.get("allocation", [])),
              ("Giải thích cảnh báo", result.get("warnings", [])))
    return [{"title": title, "points": [present(point) for point in points]} for title, points in groups]


def request_context(user, form=None):
    used = InsightReport.objects.filter(owner=user, created_at__date=timezone.localdate()).exclude(
        status="failed", error__in=NON_COUNTING_ERRORS,
    ).count()
    return {"form": form if form is not None else AnalyzeForm(), "configured": configured(),
            "remaining_requests": max(0, 5 - used)}


def latest_context(user):
    latest_log = StudyLog.objects.filter(owner=user).order_by("-created_at").values("created_at")[:1]
    report = InsightReport.objects.filter(owner=user, status=InsightReport.Status.SUCCESS).annotate(
        latest_log_at=Subquery(latest_log),
    ).first()
    if not report:
        return {"latest_insight": None}
    payload = report.snapshot.get("payload", {})
    as_of = snapshot_time(payload)
    stale = bool(as_of and timezone.is_aware(as_of) and report.latest_log_at
                 and report.latest_log_at.replace(microsecond=0) > as_of)
    groups = sections(report.result, report.snapshot)
    return {"latest_insight": report, "report_period": period_text(payload), "report_stale": stale,
            "report_summary": next(iter(groups[0]["points"]), None), "report_sections": groups,
            "highlights": [group["points"][0] for group in groups[1:] if group["points"]]}
