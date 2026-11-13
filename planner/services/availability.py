from dataclasses import dataclass
from datetime import datetime, time, timedelta

from django.db.models import Q
from django.utils import timezone

from studies.models import Task

from ..models import DAY_CHOICES, BusyEvent, StudyPreference


@dataclass(frozen=True)
class BusyOccurrence:
    event: BusyEvent
    starts_at: datetime
    ends_at: datetime


def get_preferences(user):
    return StudyPreference.objects.filter(owner=user).first() or StudyPreference(owner=user)


def at_time(day, clock):
    return timezone.make_aware(datetime.combine(day, clock))


def expand_busy_events(events, range_start, range_end):
    occurrences = []
    for event in events:
        start = timezone.localtime(event.starts_at)
        end = timezone.localtime(event.ends_at)
        if not event.repeat_weekly:
            if start < range_end and end > range_start:
                occurrences.append(BusyOccurrence(event, start, end))
            continue
        day_span = (end.date() - start.date()).days
        first_relevant_day = timezone.localtime(range_start).date() - timedelta(days=day_span)
        weeks = max(0, (first_relevant_day - start.date()).days // 7)
        occurrence_day = start.date() + timedelta(weeks=weeks)
        while True:
            occurrence_start = at_time(occurrence_day, start.time())
            if occurrence_start >= range_end:
                break
            if event.repeat_until and occurrence_day > event.repeat_until:
                break
            occurrence_end = at_time(occurrence_day + timedelta(days=day_span), end.time())
            if occurrence_end > range_start:
                occurrences.append(BusyOccurrence(event, occurrence_start, occurrence_end))
            occurrence_day += timedelta(days=7)
    return sorted(occurrences, key=lambda item: (item.starts_at, item.ends_at, item.event.pk))


def subtract_busy(window_start, window_end, blocked):
    """Subtract the union of busy intervals, using half-open [start, end) ranges."""
    free = []
    cursor = window_start
    for start, end in sorted(blocked):
        if end <= cursor or start >= window_end:
            continue
        if start > cursor:
            free.append((cursor, min(start, window_end)))
        cursor = max(cursor, end)
        if cursor >= window_end:
            break
    if cursor < window_end:
        free.append((cursor, window_end))
    return free


def available_intervals(day, preferences, blocked, now):
    if day.weekday() not in preferences.study_days:
        return []
    start = at_time(day, preferences.study_start)
    end = at_time(day, preferences.study_end)
    if now > start:
        start = timezone.localtime(now).replace(second=0, microsecond=0)
        if now.second or now.microsecond:
            start += timedelta(minutes=1)
    if start >= end:
        return []
    return subtract_busy(start, end, blocked)


def build_week(user, monday, preferences, now=None):
    now = now or timezone.now()
    week_start = at_time(monday, time.min)
    week_end = at_time(monday + timedelta(days=7), time.min)
    events = BusyEvent.objects.filter(owner=user, starts_at__lt=week_end).filter(
        Q(repeat_weekly=True) | Q(ends_at__gt=week_start)
    )
    occurrences = expand_busy_events(events, week_start, week_end)
    tasks = list(Task.objects.filter(
        owner=user, deadline__gte=week_start, deadline__lt=week_end,
    ).select_related("subject"))
    days = []
    for offset in range(7):
        day = monday + timedelta(days=offset)
        day_start, day_end = at_time(day, time.min), at_time(day + timedelta(days=1), time.min)
        items, blocked = [], []
        for occurrence in occurrences:
            if occurrence.starts_at < day_end and occurrence.ends_at > day_start:
                start, end = max(occurrence.starts_at, day_start), min(occurrence.ends_at, day_end)
                blocked.append((start, end))
                items.append({
                    "kind": "busy", "event": occurrence.event, "starts_at": start,
                    "start_label": start.strftime("%H:%M"),
                    "end_label": "24:00" if end == day_end else end.strftime("%H:%M"),
                })
        for task in tasks:
            local_deadline = timezone.localtime(task.deadline)
            if local_deadline.date() == day:
                items.append({
                    "kind": "deadline", "task": task, "starts_at": local_deadline,
                    "start_label": local_deadline.strftime("%H:%M"),
                })
        intervals = available_intervals(day, preferences, blocked, now)
        free = [
            {"start_label": start.strftime("%H:%M"), "end_label": end.strftime("%H:%M"),
             "minutes": int((end - start).total_seconds() // 60)}
            for start, end in intervals if end - start >= timedelta(minutes=1)
        ]
        days.append({
            "date": day, "label": DAY_CHOICES[day.weekday()][1],
            "is_today": day == timezone.localtime(now).date(),
            "is_past": day < timezone.localtime(now).date(),
            "items": sorted(items, key=lambda item: item["starts_at"]), "free": free,
            "capacity_minutes": min(sum(item["minutes"] for item in free), preferences.max_daily_minutes),
        })
    return days
