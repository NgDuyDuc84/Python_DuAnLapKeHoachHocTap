"""Read-only presentation of the weekly timeline."""
from datetime import time, timedelta

from django.db.models import Exists, OuterRef
from django.utils import timezone

from studies.models import Task

from .models import StudyPlan, StudySession
from .services.availability import at_time


def position_items(days):
    first_hour, last_hour = 7, 23
    for day in days:
        lanes, group = [], []
        for item in sorted(day["items"], key=lambda item: item["starts_at"]):
            start = item["starts_at"].hour * 60 + item["starts_at"].minute
            end = item.get("ends_at")
            duration = int((end - item["starts_at"]).total_seconds() / 60) if end else 30
            height = min(1440 - start, max(1, duration))
            finish = start + height
            if lanes and start >= max(lanes):
                for member in group:
                    member["lanes"] = len(lanes)
                lanes, group = [], []
            lane = next((i for i, free in enumerate(lanes) if free <= start), len(lanes))
            if lane == len(lanes):
                lanes.append(finish)
            else:
                lanes[lane] = finish
            item.update(minute=start, duration=height, lane=lane)
            group.append(item)
            first_hour = min(first_hour, start // 60)
            last_hour = max(last_hour, (finish + 59) // 60)
        for member in group:
            member["lanes"] = len(lanes)
    return {"calendar_hours": range(first_hour, last_hour), "first_minute": first_hour * 60}


def week_display(user, monday, days):
    plan = StudyPlan.objects.filter(owner=user, week_start=monday).order_by("-created_at", "-pk").first()
    draft = plan if plan and not plan.applied_at else None
    suggested = list(draft.sessions.filter(owner=user, status=StudySession.Status.PLANNED)
                     .select_related("task__subject")) if draft else []
    for session in suggested:
        start, end = timezone.localtime(session.starts_at), timezone.localtime(session.ends_at)
        for day in days:
            midnight = at_time(day["date"], time.min)
            left, right = max(start, midnight), min(end, midnight + timedelta(days=1))
            if left < right:
                day["items"].append({
                    "kind": "draft", "session": session, "starts_at": left, "ends_at": right,
                    "start_label": left.strftime("%H:%M"),
                    "end_label": right.strftime("%H:%M") if right.date() == day["date"] else "24:00",
                })
    scheduled = StudySession.objects.filter(
        owner=user, task_id=OuterRef("pk"), plan__applied_at__isnull=False,
        status=StudySession.Status.PLANNED, ends_at__gt=timezone.now(),
    )
    backlog = Task.objects.filter(owner=user).exclude(status=Task.Status.DONE).filter(
        ~Exists(scheduled),
    ).select_related("subject")
    return {**position_items(days), "unscheduled_tasks": backlog, "draft": draft, "suggestion_count": len(suggested)}
