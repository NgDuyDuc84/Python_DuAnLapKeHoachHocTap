import hashlib
import json
from datetime import timedelta

from django.utils import timezone

from focus.models import StudyLog
from focus.services import build_statistics
from planner.services.alerts import build_alerts
from planner.services.availability import build_week, get_preferences
from planner.services.scheduling import calculate_schedule
from studies.models import Task


def fingerprint(snapshot):
    return hashlib.sha256(json.dumps(snapshot, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def build_snapshot(user, *, now=None):
    now = (now or timezone.now()).replace(microsecond=0)
    today = timezone.localtime(now).date()
    start = today - timedelta(days=13)
    monday = today - timedelta(days=today.weekday())
    logs = StudyLog.objects.filter(owner=user, studied_on__range=(start, today))
    statistics = build_statistics(logs, start, today)
    schedule = calculate_schedule(user, monday, now=now)
    alerts = build_alerts(user, now=now)
    preferences = get_preferences(user)
    week = build_week(user, monday, preferences, now=now)
    tasks = list(Task.objects.filter(owner=user).exclude(status=Task.Status.DONE).select_related("subject")[:20])
    labels = {
        "H01": "Nhật ký 14 ngày", "H02": "Phút học từng ngày", "H03": "Nguồn ghi nhận",
        "H04": "Phân bổ môn trong nhật ký", "H05": "Buổi chưa ghi nhận",
        "L01": "Tùy chọn học", "L02": "Quỹ thời gian tuần hiện tại",
    }
    subjects = {}

    def subject_ref(label):
        if not label:
            return ""
        if label not in subjects:
            subjects[label] = f"M{len(subjects) + 1:02d}"
        return subjects[label]

    subject_totals = []
    for row in statistics["subjects"][:10]:
        subject_totals.append({"subject_ref": subject_ref(row["subject_label"]), "minutes": row["minutes"]})
    rows = {row["task_id"]: row for row in schedule["report"]}
    refs, task_data = {}, []
    for index, task in enumerate(tasks, 1):
        ref = refs[task.pk] = f"V{index:02d}"
        labels[ref] = task.title
        subject_label = str(task.subject) if task.subject_id else ""
        row = rows[task.pk]
        task_data.append({
            "ref": ref, "subject_ref": subject_ref(subject_label),
            "deadline": timezone.localtime(task.deadline).isoformat(),
            "priority": task.priority, "remaining_minutes": task.remaining_minutes,
            "can_split": task.can_split, "reserved_future_minutes": row["existing_minutes"],
            "proposed_week_minutes": row["scheduled_minutes"],
            "unallocated_week_minutes": row["unallocated_minutes"], "reason": row["reason"],
        })
    warnings = []

    def add_warning(task, kind, **fields):
        ref = f"C{len(warnings) + 1:02d}"
        labels[ref] = task.title
        warnings.append({"ref": ref, "task_ref": refs.get(task.pk, ""), "kind": kind, **fields})

    for row in alerts["task_alerts"]:
        if len(warnings) >= 20:
            break
        add_warning(row["task"], "overdue" if row["overdue"] else "missing_schedule", missing_minutes=row["missing"])
    for row in alerts["conflicts"]:
        if len(warnings) >= 20:
            break
        add_warning(row["session"].task, "session_conflict", starts_at=timezone.localtime(row["session"].starts_at).isoformat(), reasons=row["reasons"])
    for label, ref in subjects.items():
        labels[ref] = label
    days = [{"date": d["date"].isoformat(), "minutes": d["minutes"]} for d in statistics["days"]]
    payload = {
        "as_of": timezone.localtime(now).isoformat(), "timezone": "Asia/Ho_Chi_Minh",
        "period": {"start": start.isoformat(), "end": today.isoformat()},
        "facts": {
            "H01": {"minutes": statistics["totals"]["minutes"], "entries": statistics["totals"]["entries"],
                    "study_days": statistics["study_days"], "daily_average": statistics["daily_average"],
                    "previous_7_minutes": sum(d["minutes"] for d in days[:7]),
                    "recent_7_minutes": sum(d["minutes"] for d in days[7:])},
            "H02": days, "H03": statistics["sources"],
            "H04": {"subjects": subject_totals, "omitted_subjects": max(0, len(statistics["subjects"]) - 10)},
            "H05": {"unrecorded_sessions": alerts["unrecorded_count"]},
            "L01": {"study_days": preferences.study_days, "start": preferences.study_start.isoformat(),
                    "end": preferences.study_end.isoformat(), "max_daily_minutes": preferences.max_daily_minutes,
                    "session_minutes": preferences.session_minutes, "break_minutes": preferences.break_minutes},
            "L02": [{"date": d["date"].isoformat(), "capacity_minutes": d["capacity_minutes"]} for d in week],
        },
        "tasks": task_data, "warnings": warnings,
        "scope": {"unfinished_tasks": len(schedule["report"]), "included_tasks": len(tasks),
                  "total_warnings": len(alerts["task_alerts"]) + len(alerts["conflicts"]), "included_warnings": len(warnings)},
    }
    return {"payload": payload, "labels": labels}


def baseline_report(snapshot):
    payload = snapshot["payload"]
    totals = payload["facts"]["H01"]
    habits = (
        f"Đã ghi {totals['minutes']} phút trong {totals['study_days']}/14 ngày; trung bình {totals['daily_average']} phút/ngày. "
        "Nhật ký chưa chứng minh công việc đã hoàn thành."
        if totals["entries"] else "Chưa có nhật ký trong 14 ngày. Cần ghi nhận việc học trước khi nhận xét thói quen."
    )
    allocation = []
    for row in payload["tasks"][:5]:
        allocation.append({
            "text": f"{row['ref']}: còn {row['remaining_minutes']} phút, đã dành {row['reserved_future_minutes']} phút tương lai; "
                    f"phương án bổ sung tuần này đề xuất thêm {row['proposed_week_minutes']} phút, còn {row['unallocated_week_minutes']} phút chưa xếp. {row['reason']}",
            "evidence": [row["ref"], "L02"],
        })
    warnings = [{
        "text": "Việc đã quá hạn; cần cập nhật tiến độ hoặc xem lại hạn." if row["kind"] == "overdue"
                else "Chưa có đủ buổi tương lai trước hạn; chưa thể kết luận không còn chỗ để xếp." if row["kind"] == "missing_schedule"
                else "Buổi có xung đột: " + " ".join(row["reasons"]),
        "evidence": [row["ref"]],
    } for row in payload["warnings"][:5]]
    if payload["facts"]["H05"]["unrecorded_sessions"]:
        warnings.append({"text": "Có buổi đã kết thúc chưa ghi nhận. Hãy xác nhận đã học hoặc bỏ qua để dữ liệu phản ánh đúng thực tế.", "evidence": ["H05"]})
    return {
        "summary": {"text": "Nhận xét dưới đây được Python tính từ dữ liệu hiện có; chưa gọi AI.", "evidence": ["H01"]},
        "habits": [{"text": habits, "evidence": ["H01"]}], "allocation": allocation, "warnings": warnings,
    }
