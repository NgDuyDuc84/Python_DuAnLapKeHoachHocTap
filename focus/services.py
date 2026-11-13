from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone

from studies.models import Task

from .models import FocusSession, StudyLog


class FocusError(Exception):
    pass


def task_labels(task):
    subject = task.subject
    label = ""
    if subject:
        label = f"{subject.name} — {subject.semester}" if subject.semester else subject.name
    return {"task_title": task.title, "subject_label": label}


def lock_owner(user):
    get_user_model().objects.select_for_update().get(pk=user.pk)


def active_session(user):
    return FocusSession.objects.filter(owner=user, status__in=[FocusSession.Status.RUNNING, FocusSession.Status.PAUSED]).first()


@transaction.atomic
def start_work(user, task_id, request_key, *, now=None):
    lock_owner(user)
    previous = FocusSession.objects.filter(owner=user, request_key=request_key).first()
    if previous:
        return previous
    if active_session(user):
        raise FocusError("Bạn đang có một phiên học/nghỉ. Hãy tiếp tục hoặc kết thúc phiên đó trước.")
    task = Task.objects.select_related("subject").get(owner=user, pk=task_id)
    if task.status == Task.Status.DONE:
        raise FocusError("Chọn công việc chưa hoàn thành để bắt đầu học.")
    now = now or timezone.now()
    return FocusSession.objects.create(owner=user, task=task, request_key=request_key,
                                       started_at=now, resumed_at=now, **task_labels(task))


@transaction.atomic
def timer_action(user, pk, action, *, notes="", now=None):
    lock_owner(user)
    session = FocusSession.objects.select_for_update().get(owner=user, pk=pk)
    now = now or timezone.now()
    if action == "break":
        if session.phase != FocusSession.Phase.WORK or session.status != FocusSession.Status.FINISHED:
            raise FocusError("Kết thúc phiên học trước khi bắt đầu nghỉ.")
        existing = FocusSession.objects.filter(previous_work=session, owner=user).first()
        if existing:
            return existing
        if active_session(user):
            raise FocusError("Hãy kết thúc phiên đang chạy trước khi bắt đầu nghỉ.")
        return FocusSession.objects.create(
            owner=user, task=session.task, task_title=session.task_title, subject_label=session.subject_label,
            previous_work=session, phase=FocusSession.Phase.BREAK, duration_seconds=5 * 60,
            started_at=now, resumed_at=now,
        )
    if action == "finish" and session.status == FocusSession.Status.FINISHED:
        return session
    if action == "cancel" and session.status == FocusSession.Status.CANCELLED:
        return session
    if not session.is_active:
        raise FocusError("Phiên đã kết thúc hoặc đã hủy; không thể thực hiện thao tác này.")
    elapsed = session.elapsed(now)
    if action == "pause":
        if session.status == FocusSession.Status.PAUSED:
            return session
        session.elapsed_seconds, session.resumed_at = elapsed, None
        session.status = FocusSession.Status.PAUSED
    elif action == "resume":
        if elapsed >= session.duration_seconds:
            raise FocusError("Đã hết giờ. Hãy kết thúc phiên để lưu kết quả.")
        if session.status == FocusSession.Status.RUNNING:
            return session
        session.resumed_at, session.status = now, FocusSession.Status.RUNNING
    elif action in ("finish", "cancel"):
        session.elapsed_seconds, session.resumed_at, session.finished_at = elapsed, None, now
        session.status = FocusSession.Status.FINISHED if action == "finish" else FocusSession.Status.CANCELLED
        if action == "finish" and session.phase == FocusSession.Phase.WORK and elapsed >= 60:
            StudyLog.objects.create(
                owner=user, task=session.task, task_title=session.task_title, subject_label=session.subject_label,
                studied_on=timezone.localdate(session.started_at), minutes=elapsed // 60, notes=notes,
                source=StudyLog.Source.POMODORO, focus_session=session,
            )
    else:
        raise FocusError("Thao tác không hợp lệ.")
    session.save(update_fields=["elapsed_seconds", "resumed_at", "finished_at", "status"])
    return session


@transaction.atomic
def add_manual_log(user, data):
    lock_owner(user)
    existing = StudyLog.objects.filter(owner=user, entry_key=data["entry_key"]).first()
    if existing:
        return existing
    task = Task.objects.select_related("subject").get(owner=user, pk=data["task"].pk)
    log = StudyLog(owner=user, task=task, studied_on=data["studied_on"], minutes=data["minutes"],
                   notes=data["notes"], entry_key=data["entry_key"], **task_labels(task))
    log.full_clean()
    log.save()
    return log


def build_statistics(logs, start, end):
    totals = logs.aggregate(minutes=Sum("minutes", default=0), entries=Count("pk"))
    by_day = {row["studied_on"]: row["minutes"] for row in logs.order_by().values("studied_on").annotate(minutes=Sum("minutes"))}
    days = [{"date": start + timedelta(days=i), "minutes": by_day.get(start + timedelta(days=i), 0)}
            for i in range((end - start).days + 1)]
    maximum = max((d["minutes"] for d in days), default=0)
    for day in days:
        day["width"] = round(day["minutes"] / maximum * 100) if maximum else 0
    subjects = list(logs.order_by().values("subject_label").annotate(minutes=Sum("minutes")).order_by("-minutes", "subject_label"))
    sources = list(logs.order_by().values("source").annotate(minutes=Sum("minutes"), entries=Count("pk")).order_by("source"))
    return {"totals": totals, "days": days, "subjects": subjects, "sources": sources,
            "study_days": len(by_day), "daily_average": round(totals["minutes"] / len(days), 1)}
