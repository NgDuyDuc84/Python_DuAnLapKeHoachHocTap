from datetime import timedelta

from django.utils import timezone

from studies.models import Task

from ..models import BusyEvent, StudySession
from .availability import get_preferences
from .scheduling import ceil_minute, minutes_between
from .sessions import session_conflicts


def build_task_alerts(tasks, sessions, now):
    """Shared deadline/shortfall calculation; inputs are already scoped to the owner."""
    task_alerts = []
    for task in tasks:
        credit = sum(
            minutes_between(max(s.starts_at, ceil_minute(now)), min(s.ends_at, task.deadline))
            for s in sessions if s.task_id == task.pk and s.status == StudySession.Status.PLANNED
        )
        missing = max(0, task.remaining_minutes - credit)
        if task.deadline <= now or missing:
            task_alerts.append({"task": task, "missing": missing, "overdue": task.deadline <= now})
    return task_alerts


def build_alerts(user, *, now=None):
    now = now or timezone.now()
    horizon = now + timedelta(days=7)
    sessions = list(StudySession.objects.filter(
        owner=user, plan__applied_at__isnull=False,
    ).exclude(status=StudySession.Status.CANCELLED).select_related("task", "plan"))
    tasks = Task.objects.filter(owner=user, deadline__lte=horizon).exclude(status=Task.Status.DONE)
    task_alerts = build_task_alerts(tasks, sessions, now)
    preferences = get_preferences(user)
    events = list(BusyEvent.objects.filter(owner=user))
    conflicts = []
    for session in sessions:
        if session.status == StudySession.Status.PLANNED and now < session.ends_at and session.starts_at < horizon:
            errors = session_conflicts(session, preferences, events, sessions)
            allocated = sum(
                minutes_between(max(s.starts_at, ceil_minute(now)), min(s.ends_at, session.task.deadline))
                for s in sessions if s.task_id == session.task_id and s.status == StudySession.Status.PLANNED
            )
            if allocated > session.task.remaining_minutes:
                errors.append("Phút đã xếp trong tương lai vượt thời lượng công việc còn lại.")
            if errors:
                conflicts.append({"session": session, "reasons": errors})
    unrecorded = sorted(
        [s for s in sessions if s.status == StudySession.Status.PLANNED and s.ends_at <= now],
        key=lambda s: s.ends_at, reverse=True,
    )
    return {"task_alerts": task_alerts, "conflicts": conflicts,
            "unrecorded": unrecorded[:20], "unrecorded_count": len(unrecorded), "horizon": horizon}
