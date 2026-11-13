from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from studies.models import Task

from ..models import BusyEvent, StudySession
from .availability import at_time, expand_busy_events, get_preferences
from .scheduling import PlanError, ceil_minute, minutes_between


def session_conflicts(session, preferences, events, others):
    """Current constraints, also used to explain conflicts on the alerts page."""
    errors = []
    start, end = timezone.localtime(session.starts_at), timezone.localtime(session.ends_at)
    if session.task.status == Task.Status.DONE:
        errors.append("Công việc đã hoàn thành nhưng buổi chưa được hủy.")
    if end > session.task.deadline:
        errors.append("Buổi học vượt deadline hiện tại.")
    if (start.weekday() not in preferences.study_days or start.time() < preferences.study_start
            or end.time() > preferences.study_end or start.date() != end.date()):
        errors.append("Buổi học nằm ngoài ngày hoặc khung giờ được học.")
    if expand_busy_events(events, start, end):
        errors.append("Buổi học trùng lịch bận.")
    gap = timedelta(minutes=preferences.break_minutes)
    others = [s for s in others if s.pk != session.pk and s.status != StudySession.Status.CANCELLED]
    if any(s.starts_at < end + gap and s.ends_at > start - gap for s in others):
        errors.append("Trùng buổi khác hoặc không đủ thời gian nghỉ.")
    day_start, day_end = at_time(start.date(), time.min), at_time(start.date() + timedelta(days=1), time.min)
    used = session.duration_minutes + sum(
        minutes_between(max(s.starts_at, day_start), min(s.ends_at, day_end)) for s in others
    )
    if used > preferences.max_daily_minutes:
        errors.append("Tổng phút học vượt giới hạn ngày hiện tại.")
    return errors


def editable_session(user, pk):
    get_user_model().objects.select_for_update().get(pk=user.pk)
    session = StudySession.objects.select_for_update().select_related("plan", "task").get(
        pk=pk, owner=user, plan__applied_at__isnull=False,
    )
    if session.status != StudySession.Status.PLANNED:
        raise PlanError("Buổi đã được ghi nhận hoặc hủy; không thể thực hiện lại thao tác.")
    return session


@transaction.atomic
def move_session(user, pk, starts_at, ends_at, *, now=None):
    session = editable_session(user, pk)
    now = now or timezone.now()
    if session.is_locked:
        raise PlanError("Mở khóa buổi trước khi chỉnh giờ.")
    if session.starts_at <= now or starts_at <= now:
        raise PlanError("Chỉ được chỉnh buổi chưa bắt đầu sang một thời điểm tương lai.")
    if any(value.second or value.microsecond for value in (starts_at, ends_at)):
        raise PlanError("Giờ buổi học phải tròn phút.")
    session.starts_at, session.ends_at = starts_at, ends_at
    try:
        session.full_clean()
    except ValidationError as error:
        raise PlanError(" ".join(error.messages)) from error
    others = list(StudySession.objects.filter(owner=user, plan__applied_at__isnull=False).exclude(pk=pk).exclude(status=StudySession.Status.CANCELLED))
    errors = session_conflicts(session, get_preferences(user), list(BusyEvent.objects.filter(owner=user)), others)
    credit = sum(
        minutes_between(max(s.starts_at, ceil_minute(now)), min(s.ends_at, session.task.deadline))
        for s in others if s.task_id == session.task_id and s.status == StudySession.Status.PLANNED
    )
    if session.duration_minutes + credit > session.task.remaining_minutes:
        errors.append("Số phút đã xếp vượt thời lượng công việc còn lại; hãy giảm độ dài buổi.")
    if not session.task.can_split and (credit or session.duration_minutes != session.task.remaining_minutes):
        errors.append("Công việc không chia buổi cần toàn bộ thời lượng còn lại trong một buổi.")
    if errors:
        raise PlanError(" ".join(errors))
    session.is_manual = True
    session.save(update_fields=["starts_at", "ends_at", "is_manual"])
    return session


@transaction.atomic
def set_session_lock(user, pk, locked):
    session = editable_session(user, pk)
    session.is_locked = locked
    session.save(update_fields=["is_locked"])
    return session


@transaction.atomic
def record_session(user, pk, result, remaining_minutes, *, now=None):
    session = editable_session(user, pk)
    now = now or timezone.now()
    task = Task.objects.select_for_update().get(pk=session.task_id, owner=user)
    if result not in (StudySession.Status.DONE, StudySession.Status.CANCELLED) or not 0 <= remaining_minutes <= 2147483647:
        raise PlanError("Kết quả buổi học hoặc thời lượng còn lại không hợp lệ.")
    if result == StudySession.Status.DONE and session.starts_at > now:
        raise PlanError("Chưa thể ghi nhận đã học cho một buổi trong tương lai.")
    if result == StudySession.Status.CANCELLED and session.is_locked:
        raise PlanError("Mở khóa buổi trước khi hủy hoặc bỏ qua.")
    if result == StudySession.Status.CANCELLED and remaining_minutes != task.remaining_minutes:
        raise PlanError("Hủy/bỏ qua buổi không đổi tiến độ. Giữ nguyên phút còn lại hoặc cập nhật ở trang công việc.")
    if result == StudySession.Status.DONE:
        task.remaining_minutes = remaining_minutes
        task.status = Task.Status.DONE if remaining_minutes == 0 else Task.Status.IN_PROGRESS
        task.save(update_fields=["remaining_minutes", "status"])
    session.status = result
    session.save(update_fields=["status"])
    return session
