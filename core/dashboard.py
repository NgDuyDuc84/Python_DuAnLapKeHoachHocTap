from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Exists, Q, Sum
from django.utils import timezone

from focus.forms import FocusStartForm
from focus.models import StudyLog
from focus.services import active_session
from planner.models import StudyPlan, StudySession
from planner.services.alerts import build_task_alerts
from studies.models import Subject, Task


WEEKDAYS = ("Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ nhật")


def button(label, url, *, pk=None, task_id=None):
    return {"label": label, "url": url, "pk": pk, "task_id": task_id,
            "method": "post" if task_id is not None else "get"}


def select_dashboard_action(*, now, active_focus, sessions, unrecorded, task_alerts,
                            has_subjects, has_tasks, has_plan):
    """Pure priority selector: no queries, clock reads, forms or mutations."""
    def result(kind, title, primary=None, *, secondary=None, task=None, session=None):
        return {"kind": kind, "title": title, "primary": primary, "secondary": secondary,
                "task": task, "session": session}

    if active_focus:
        return result("focus", f"Tiếp tục phiên: {active_focus.task_title}",
                      button("Tiếp tục", "focus:session", pk=active_focus.pk))
    ongoing = next((s for s in sessions if s.status == StudySession.Status.PLANNED
                    and s.starts_at <= now < s.ends_at), None)
    if ongoing:
        return result("ongoing", f"Đang diễn ra: {ongoing.task.title}",
                      button("Bắt đầu tập trung", "focus:home", task_id=ongoing.task_id),
                      secondary=button("Ghi nhận", "planner:session_record", pk=ongoing.pk),
                      task=ongoing.task, session=ongoing)
    if unrecorded:
        return result("unrecorded", f"Buổi chưa ghi nhận: {unrecorded.task.title}",
                      button("Ghi nhận buổi này", "planner:session_record", pk=unrecorded.pk),
                      task=unrecorded.task, session=unrecorded)
    overdue = next((row["task"] for row in task_alerts if row["overdue"]), None)
    if overdue:
        return result("overdue", f"{overdue.title} đã quá hạn",
                      button("Cập nhật tiến độ", "studies:task_progress", pk=overdue.pk),
                      secondary=button("Xếp lịch", "planner:plan_generate"), task=overdue)
    shortfall = next((row["task"] for row in task_alerts if row["missing"] and not row["overdue"]
                      and now < row["task"].deadline <= now + timedelta(days=7)), None)
    if shortfall:
        return result("shortfall", f"{shortfall.title} chưa đủ lịch trước hạn",
                      button("Xếp lịch", "planner:plan_generate"),
                      secondary=button("Học ngay", "focus:home", task_id=shortfall.pk), task=shortfall)
    upcoming = next((s for s in sessions if s.status == StudySession.Status.PLANNED
                     and s.starts_at > now and s.starts_at.astimezone(now.tzinfo).date() == now.date()), None)
    if upcoming:
        start = upcoming.starts_at.astimezone(now.tzinfo).strftime("%H:%M")
        return result("upcoming", f"Buổi tiếp theo: {upcoming.task.title} lúc {start}",
                      button("Xem lịch", "planner:week"), task=upcoming.task, session=upcoming)
    if not (has_subjects and has_tasks and has_plan):
        return result("onboarding", "Chuẩn bị kế hoạch đầu tiên")
    return result("ready", "Bạn đã sẵn sàng", button("Bắt đầu tập trung", "focus:home"))


def deadline_details(task, now):
    day = task.deadline.astimezone(now.tzinfo).date()
    days = (day - now.date()).days
    overdue = task.deadline <= now
    relative = (f"quá hạn {abs(days)} ngày" if days < 0 else "quá hạn hôm nay") if overdue else (
        f"còn {days} ngày" if days else "đến hạn hôm nay")
    return {"label": f"{WEEKDAYS[day.weekday()]} {day:%d/%m}", "relative": relative,
            "countdown": f"{abs(days)} ngày" if days else "Hôm nay", "overdue": overdue}


def prepare_button(action, user):
    if action and action["method"] == "post":
        action["form"] = FocusStartForm(user=user, auto_id=False)
    return action


def build_dashboard(user, *, now=None):
    now = timezone.localtime(now or timezone.now())
    today = now.date()
    day_start = timezone.make_aware(datetime.combine(today, time.min))
    day_end = day_start + timedelta(days=1)
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=7)
    week_boundary = timezone.make_aware(datetime.combine(week_start, time.min))
    week_limit = timezone.make_aware(datetime.combine(week_end, time.min))
    horizon = now + timedelta(days=7)
    tasks = list(Task.objects.filter(owner=user).filter(
        (~Q(status=Task.Status.DONE) & Q(deadline__lte=horizon)) |
        Q(deadline__gte=week_boundary, deadline__lt=week_limit),
    ).select_related("subject"))
    urgent_tasks = [task for task in tasks if task.status != Task.Status.DONE and task.deadline <= horizon]
    applied = StudySession.objects.filter(owner=user, plan__applied_at__isnull=False).exclude(
        status=StudySession.Status.CANCELLED,
    ).select_related("task__subject", "plan")
    sessions = list(applied.filter(Q(starts_at__gte=week_boundary) | Q(ends_at__gt=now)).filter(starts_at__lt=horizon))
    unrecorded = applied.filter(status=StudySession.Status.PLANNED, ends_at__lte=now).order_by(
        "-ends_at", "starts_at", "pk",
    ).first()
    task_alerts = build_task_alerts(urgent_tasks, sessions, now)
    alerts_by_task = {row["task"].pk: row for row in task_alerts}
    today_sessions = [s for s in sessions if day_start <= s.starts_at < day_end]
    focus = active_session(user)
    has_subjects, has_tasks, has_plan = get_user_model().objects.filter(pk=user.pk).values_list(
        Exists(Subject.objects.filter(owner=user)), Exists(Task.objects.filter(owner=user)),
        Exists(StudyPlan.objects.filter(owner=user)),
    ).get()
    action = select_dashboard_action(now=now, active_focus=focus, sessions=sessions, unrecorded=unrecorded,
                                     task_alerts=task_alerts, has_subjects=has_subjects,
                                     has_tasks=has_tasks, has_plan=has_plan)
    for key in ("primary", "secondary"):
        prepare_button(action[key], user)
    if action["task"]:
        action["deadline"] = deadline_details(action["task"], now)
    groups = {today: {"date": today, "label": "Hôm nay", "rows": []}}
    visible = [s for s in sessions if s.starts_at >= day_start
               and (s.starts_at < day_end or s.status == StudySession.Status.PLANNED)][:6]
    for session in visible:
        day = timezone.localdate(session.starts_at)
        label = "Hôm nay" if day == today else "Ngày mai" if day == today + timedelta(days=1) else WEEKDAYS[day.weekday()]
        group = groups.setdefault(day, {"date": day, "label": label, "rows": []})
        row_action = None
        if session.status == StudySession.Status.PLANNED:
            row_action = button("Ghi nhận", "planner:session_record", pk=session.pk) if session.ends_at <= now else (
                button("Bắt đầu", "focus:home", task_id=session.task_id))
        group["rows"].append({"session": session, "action": prepare_button(row_action, user)})
    task_rows = [{"task": task, "missing": alerts_by_task.get(task.pk, {}).get("missing", 0),
                  "deadline": deadline_details(task, now),
                  "start": prepare_button(button("Học ngay", "focus:home", task_id=task.pk), user),
                  "progress": button("Tiến độ", "studies:task_progress", pk=task.pk)} for task in urgent_tasks[:6]]
    week_days = []
    for offset in range(7):
        day = week_start + timedelta(days=offset)
        week_days.append({"date": day, "label": ("T2", "T3", "T4", "T5", "T6", "T7", "CN")[offset],
                          "today": day == today,
                          "sessions": sum(timezone.localdate(s.starts_at) == day for s in sessions),
                          "deadlines": sum(timezone.localdate(task.deadline) == day for task in tasks)})
    due_soon = sum(now < task.deadline <= horizon for task in urgent_tasks)
    summary = f"Hôm nay có {len(today_sessions)} buổi học" if today_sessions else "Hôm nay chưa có buổi học nào"
    if due_soon:
        summary += f"; {due_soon} việc đến hạn trong 7 ngày"
    return {
        "today": today, "weekday": WEEKDAYS[today.weekday()], "summary": summary + ".", "action": action,
        "today_count": len(today_sessions), "today_done": sum(s.status == StudySession.Status.DONE for s in today_sessions),
        "weekly_minutes": StudyLog.objects.filter(owner=user, studied_on__range=(today - timedelta(days=6), today)).aggregate(
            minutes=Sum("minutes", default=0))["minutes"],
        "shell_overdue_count": (overdue_count := sum(row["overdue"] for row in task_alerts)),
        "overdue_count": overdue_count, "due_soon_count": due_soon,
        "upcoming_sessions": [s for s in sessions if s.status == StudySession.Status.PLANNED and s.ends_at > now][:6],
        "urgent_tasks": urgent_tasks[:6], "task_rows": task_rows, "session_groups": list(groups.values()),
        "active_focus": focus, "has_subjects": has_subjects, "has_tasks": has_tasks, "has_plan": has_plan,
        "onboarding_steps": (
            {"title": "Thêm môn học", "done": has_subjects, "url": "studies:subject_create"},
            {"title": "Thêm công việc", "done": has_tasks, "url": "studies:task_create"},
            {"title": "Tạo kế hoạch tuần", "done": has_plan, "url": "planner:plan_generate"},
        ),
        "week_start": week_start, "week_end": week_end - timedelta(days=1), "week_days": week_days,
    }
