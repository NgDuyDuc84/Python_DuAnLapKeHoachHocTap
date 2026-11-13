"""Greedy weekly allocation: earliest deadline, then highest priority."""
import hashlib
import json
from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from studies.models import Task

from ..models import BusyEvent, StudyPlan, StudySession
from .availability import (
    at_time, available_intervals, expand_busy_events, get_preferences, subtract_busy,
)


class PlanError(Exception):
    pass


def ceil_minute(value):
    rounded = value.replace(second=0, microsecond=0)
    return rounded + timedelta(minutes=bool(value.second or value.microsecond))


def minutes_between(start, end):
    return max(0, int((end - start).total_seconds() // 60))


def calculate_schedule(user, monday, *, now=None, exclude_plan_id=None, mode=StudyPlan.Mode.ADD):
    now = now or timezone.now()
    preferences = get_preferences(user)
    start, end = at_time(monday, time.min), at_time(monday + timedelta(days=7), time.min)
    gap = timedelta(minutes=preferences.break_minutes)
    tasks = list(Task.objects.filter(owner=user).exclude(status=Task.Status.DONE))
    events = list(BusyEvent.objects.filter(owner=user).order_by("pk"))
    all_sessions = list(StudySession.objects.filter(
        owner=user, plan__applied_at__isnull=False,
    ).filter(
        Q(ends_at__gt=now) | Q(ends_at__gt=start - gap, starts_at__lt=end + gap)
    ).exclude(plan_id=exclude_plan_id).order_by("pk"))

    # Only server-owned inputs enter the preview. Hash changes invalidate old drafts.
    snapshot = {
        "preferences": [preferences.study_days, preferences.study_start, preferences.study_end,
                        preferences.max_daily_minutes, preferences.session_minutes, preferences.break_minutes],
        "tasks": [[t.pk, t.title, t.subject_id, t.deadline, t.priority, t.status,
                   t.estimated_minutes, t.remaining_minutes, t.can_split] for t in tasks],
        "busy": [[e.pk, e.title, e.starts_at, e.ends_at, e.repeat_weekly, e.repeat_until] for e in events],
        "sessions": [[s.pk, s.task_id, s.starts_at, s.ends_at, s.status, s.is_locked, s.is_manual] for s in all_sessions],
    }
    fingerprint = hashlib.sha256(json.dumps(snapshot, default=str, sort_keys=True).encode()).hexdigest()
    replacement_ids = [
        s.pk for s in all_sessions
        if mode == StudyPlan.Mode.REPLACE and s.status == StudySession.Status.PLANNED
        and not s.is_locked and not s.is_manual and s.starts_at > now
        and start <= s.starts_at < end
    ]
    existing = [s for s in all_sessions if s.pk not in replacement_ids and s.status != StudySession.Status.CANCELLED]
    occurrences = expand_busy_events(events, start, end)
    blocked = [(o.starts_at, o.ends_at) for o in occurrences]
    blocked += [(s.starts_at - gap, s.ends_at + gap) for s in existing]
    days = []
    for offset in range(7):
        day = monday + timedelta(days=offset)
        day_start, day_end = at_time(day, time.min), at_time(day + timedelta(days=1), time.min)
        used = sum(minutes_between(max(s.starts_at, day_start), min(s.ends_at, day_end)) for s in existing)
        days.append({
            "free": available_intervals(day, preferences, blocked, now),
            "budget": max(0, preferences.max_daily_minutes - used),
        })

    proposals, report = [], []
    for task in tasks:
        credit = sum(
            minutes_between(max(s.starts_at, ceil_minute(now)), min(s.ends_at, task.deadline))
            for s in existing if s.task_id == task.pk and s.status == StudySession.Status.PLANNED
        )
        need = max(0, task.remaining_minutes - credit)
        scheduled = 0
        partial_unsplittable = not task.can_split and credit > 0 and need > 0
        if not partial_unsplittable:
            for day in days:
                while need and day["budget"]:
                    choice = None
                    for slot_start, slot_end in day["free"]:
                        slot_start = ceil_minute(slot_start)
                        capacity = min(minutes_between(slot_start, min(slot_end, task.deadline)), day["budget"])
                        if not task.can_split and capacity < need:
                            continue
                        length = min(need, capacity, preferences.session_minutes) if task.can_split else need
                        if length > 0:
                            choice = (slot_start, slot_start + timedelta(minutes=length), length)
                            break
                    if choice is None:
                        break
                    slot_start, slot_end, length = choice
                    proposals.append((task.pk, slot_start, slot_end))
                    need -= length
                    scheduled += length
                    day["budget"] -= length
                    # Reserve breaks on both sides, including across midnight/week boundaries.
                    for other_day in days:
                        other_day["free"] = [
                            interval for a, b in other_day["free"]
                            for interval in subtract_busy(a, b, [(slot_start - gap, slot_end + gap)])
                        ]
        reason = "Đã có đủ thời gian trong các buổi tương lai đã áp dụng." if not scheduled and not need else "Đã bố trí đủ thời lượng."
        if need:
            if task.deadline <= now:
                reason = "Đã quá hạn; cần điều chỉnh deadline hoặc thời lượng."
            elif task.deadline <= start:
                reason = "Deadline nằm trước tuần đã chọn."
            elif partial_unsplittable:
                reason = "Công việc không chia buổi đã có lịch một phần; cần rà soát lịch đã áp dụng."
            elif task.deadline > end:
                reason = "Chưa bố trí hết trong tuần này; có thể cần thêm các tuần sau trước deadline."
            elif not task.can_split:
                reason = "Không có khoảng liên tục đủ dài trước deadline trong giới hạn ngày."
            else:
                reason = "Không đủ khoảng trống trước deadline trong các ngày và giới hạn đã chọn."
        report.append({
            "task_id": task.pk, "title": task.title, "deadline": task.deadline.isoformat(),
            "remaining_minutes": task.remaining_minutes, "existing_minutes": credit,
            "scheduled_minutes": scheduled, "unallocated_minutes": need, "reason": reason,
        })
    return {"fingerprint": fingerprint, "sessions": sorted(proposals, key=lambda s: (s[1], s[0])),
            "report": report, "replacement_ids": replacement_ids}


@transaction.atomic
def create_draft(user, monday, *, now=None, mode=StudyPlan.Mode.ADD):
    result = calculate_schedule(user, monday, now=now, mode=mode)
    plan = StudyPlan.objects.create(
        owner=user, week_start=monday, input_fingerprint=result["fingerprint"], report=result["report"],
        mode=mode, replacement_ids=result["replacement_ids"],
    )
    StudySession.objects.bulk_create([
        StudySession(owner=user, plan=plan, task_id=task_id, starts_at=start, ends_at=end)
        for task_id, start, end in result["sessions"]
    ])
    return plan


@transaction.atomic
def apply_plan(user, plan_id, *, now=None):
    # Serialize applications by the same owner on databases supporting row locks.
    get_user_model().objects.select_for_update().get(pk=user.pk)
    plan = StudyPlan.objects.select_for_update().get(pk=plan_id, owner=user)
    if plan.applied_at:
        return plan, False
    now = now or timezone.now()
    stored = list(plan.sessions.order_by("starts_at", "task_id").values_list("task_id", "starts_at", "ends_at"))
    if not stored and not plan.replacement_ids:
        raise PlanError("Không có buổi học mới để áp dụng. Hãy xem báo cáo và điều chỉnh dữ liệu.")
    # This write also obtains SQLite's writer lock. Exceptions roll it back.
    StudyPlan.objects.filter(pk=plan.pk, applied_at__isnull=True).update(applied_at=now)
    fresh = calculate_schedule(user, plan.week_start, now=now, exclude_plan_id=plan.pk, mode=plan.mode)
    if (fresh["fingerprint"] != plan.input_fingerprint or fresh["sessions"] != stored
            or fresh["replacement_ids"] != plan.replacement_ids):
        raise PlanError("Dữ liệu hoặc thời gian đã thay đổi. Hãy tạo bản xem trước mới rồi kiểm tra lại trước khi áp dụng.")
    StudySession.objects.filter(owner=user, pk__in=plan.replacement_ids).update(status=StudySession.Status.CANCELLED)
    plan.applied_at = now
    return plan, True
