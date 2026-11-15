from datetime import datetime, time, timedelta

from django.db.models import Sum
from django.utils import timezone

from focus.models import StudyLog
from focus.services import active_session
from notifications.models import Reminder
from planner.models import StudySession
from studies.models import Subject, Task


def build_dashboard(user, *, now=None):
    now = now or timezone.now()
    today = timezone.localdate(now)
    day_start = timezone.make_aware(datetime.combine(today, time.min))
    day_end = timezone.make_aware(datetime.combine(today + timedelta(days=1), time.min))
    tasks = Task.objects.filter(owner=user).exclude(status=Task.Status.DONE)
    sessions = StudySession.objects.filter(owner=user, plan__applied_at__isnull=False)
    today_sessions = sessions.filter(starts_at__gte=day_start, starts_at__lt=day_end).exclude(
        status=StudySession.Status.CANCELLED,
    )
    return {
        "today": today,
        "today_count": today_sessions.count(),
        "today_done": today_sessions.filter(status=StudySession.Status.DONE).count(),
        "weekly_minutes": StudyLog.objects.filter(
            owner=user, studied_on__range=(today - timedelta(days=6), today),
        ).aggregate(minutes=Sum("minutes", default=0))["minutes"],
        "overdue_count": tasks.filter(deadline__lt=now).count(),
        "unread_count": Reminder.objects.filter(
            owner=user, channel=Reminder.Channel.IN_APP, status=Reminder.Status.SENT, read_at__isnull=True,
        ).count(),
        "upcoming_sessions": list(sessions.filter(
            status=StudySession.Status.PLANNED, ends_at__gt=now, starts_at__lt=now + timedelta(days=7),
        ).select_related("task", "plan")[:6]),
        "urgent_tasks": list(tasks.filter(deadline__lte=now + timedelta(days=7)).select_related("subject")[:6]),
        "active_focus": active_session(user),
        "has_subjects": Subject.objects.filter(owner=user).exists(),
        "has_tasks": Task.objects.filter(owner=user).exists(),
    }
