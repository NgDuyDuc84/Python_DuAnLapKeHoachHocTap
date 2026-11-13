import hashlib
import smtplib
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db.models import F
from django.urls import reverse
from django.utils import timezone

from planner.models import StudySession
from studies.models import Task

from .models import Reminder, ReminderPreference

MAX_ATTEMPTS = 3


def get_preferences(user):
    return ReminderPreference.objects.filter(owner=user).first() or ReminderPreference(owner=user)


def reminder_text(kind, task, target_at):
    label = "Sắp đến deadline" if kind == Reminder.Kind.DEADLINE else "Sắp tới buổi học"
    title = f"{label}: {task.title}".replace("\r", " ").replace("\n", " ")
    clock = timezone.localtime(target_at).strftime("%d/%m/%Y %H:%M")
    return title, f"{task.title}\nThời điểm: {clock} (giờ Việt Nam).\nCông việc còn {task.remaining_minutes} phút."


def enqueue_due_reminders(*, now=None):
    now = now or timezone.now()
    created = 0
    for user in get_user_model().objects.filter(is_active=True).iterator():
        preferences = get_preferences(user)
        channels = [channel for channel, enabled in (
            (Reminder.Channel.IN_APP, preferences.in_app_enabled),
            (Reminder.Channel.EMAIL, preferences.email_enabled),
        ) if enabled]
        if not channels:
            continue
        tasks = Task.objects.filter(owner=user, deadline__gt=now,
                                    deadline__lte=now + timedelta(minutes=preferences.deadline_minutes)).exclude(status=Task.Status.DONE)
        sessions = StudySession.objects.filter(owner=user, plan__applied_at__isnull=False,
            status=StudySession.Status.PLANNED, starts_at__gt=now,
            starts_at__lte=now + timedelta(minutes=preferences.session_minutes)).exclude(task__status=Task.Status.DONE).select_related("task")
        events = [(Reminder.Kind.DEADLINE, t, None, t.deadline, preferences.deadline_minutes) for t in tasks]
        events += [(Reminder.Kind.SESSION, s.task, s, s.starts_at, preferences.session_minutes) for s in sessions]
        for kind, task, session, target, lead in events:
            identity = session.pk if session else task.pk
            key = hashlib.sha256(f"{kind}:{identity}:{target.isoformat()}".encode()).hexdigest()
            title, message = reminder_text(kind, task, target)
            for channel in channels:
                reminder, was_created = Reminder.objects.get_or_create(
                    owner=user, channel=channel, dedup_key=key,
                    defaults={"task": task, "study_session": session, "kind": kind, "target_at": target,
                              "remind_at": target - timedelta(minutes=lead), "title": title, "message": message,
                              "next_attempt_at": now},
                )
                created += was_created
                # Re-enable a skipped event only while it is still eligible and has attempts left.
                if reminder.status == Reminder.Status.SKIPPED and reminder.attempts < MAX_ATTEMPTS:
                    Reminder.objects.filter(pk=reminder.pk, status=Reminder.Status.SKIPPED).update(
                        status=Reminder.Status.PENDING, next_attempt_at=now, last_error="",
                    )
    return created


def current_target(reminder, preferences, now):
    if not reminder.owner.is_active:
        return None, "Tài khoản đang bị khóa."
    enabled = preferences.in_app_enabled if reminder.channel == Reminder.Channel.IN_APP else preferences.email_enabled
    if not enabled:
        return None, "Kênh nhắc đã được tắt."
    task = reminder.task
    if not task or task.owner_id != reminder.owner_id or task.status == Task.Status.DONE:
        return None, "Công việc đã xóa hoặc hoàn thành."
    if reminder.kind == Reminder.Kind.DEADLINE:
        target, lead = task.deadline, preferences.deadline_minutes
    else:
        session = reminder.study_session
        if (not session or session.owner_id != reminder.owner_id or session.task_id != task.pk
                or not session.plan.applied_at or session.status != StudySession.Status.PLANNED):
            return None, "Buổi học đã xóa, hủy, ghi nhận hoặc chưa áp dụng."
        target, lead = session.starts_at, preferences.session_minutes
    if target != reminder.target_at:
        return None, "Thời điểm đã đổi; nhắc cũ được bỏ qua."
    if target <= now:
        return None, "Thời điểm đã qua; không gửi nhắc muộn."
    return target - timedelta(minutes=lead), ""


def dispatch_one(pk, *, now=None):
    now = now or timezone.now()
    token = uuid.uuid4()
    claimed = Reminder.objects.filter(pk=pk, status__in=[Reminder.Status.PENDING, Reminder.Status.FAILED],
        next_attempt_at__lte=now, attempts__lt=MAX_ATTEMPTS).update(
            status=Reminder.Status.SENDING, claim_token=token, claimed_at=now,
        )
    if not claimed:
        return False
    reminder = Reminder.objects.select_related("owner", "task", "study_session__plan").get(pk=pk)
    owned_claim = Reminder.objects.filter(pk=pk, status=Reminder.Status.SENDING, claim_token=token)
    preferences = get_preferences(reminder.owner)
    due_at, reason = current_target(reminder, preferences, now)
    result = {"claim_token": None, "claimed_at": None}
    if reason:
        owned_claim.update(**result, status=Reminder.Status.SKIPPED, last_error=reason)
        return False
    if due_at > now:
        owned_claim.update(**result, status=Reminder.Status.PENDING, remind_at=due_at, next_attempt_at=due_at)
        return False
    title, message = reminder_text(reminder.kind, reminder.task, reminder.target_at)
    if reminder.channel == Reminder.Channel.IN_APP:
        updated = owned_claim.update(**result, status=Reminder.Status.SENT, delivered_at=now, title=title, message=message, last_error="")
        return updated == 1
    owned_claim.update(attempts=F("attempts") + 1)
    status, error = Reminder.Status.SENT, ""
    try:
        validate_email(reminder.owner.email)
        body = (f"{message}\n\nMở trong Nhịp Học: {settings.SITE_URL.rstrip('/')}{reminder.target_url}"
                f"\n\nĐổi/tắt email nhắc tại: {settings.SITE_URL.rstrip('/')}{reverse('notifications:preferences')}")
        sent = send_mail(title, body, settings.DEFAULT_FROM_EMAIL, [reminder.owner.email], fail_silently=False)
        if sent != 1:
            status, error = Reminder.Status.FAILED, "Hệ thống gửi chưa nhận email; sẽ thử lại nếu còn lượt."
    except (ValidationError, ValueError, smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused,
            smtplib.SMTPResponseException, ConnectionRefusedError):
        status, error = Reminder.Status.FAILED, "Email bị từ chối hoặc cấu hình chưa hợp lệ. Kiểm tra địa chỉ/cấu hình gửi; tối đa 3 lần tự thử."
    except (smtplib.SMTPException, OSError):
        status, error = Reminder.Status.UNCERTAIN, "Mất kết nối khi gửi, chưa xác nhận kết quả. Kiểm tra hộp thư trước khi yêu cầu gửi lại."
    test_backend = any(name in settings.EMAIL_BACKEND for name in (".console.", ".locmem.", ".filebased.", ".dummy."))
    delivery_mode = "kiểm thử, không gửi tới hộp thư" if test_backend else "máy chủ gửi email"
    message += f"\nEmail nhận tại lần thử: {reminder.owner.email}.\nChế độ tại lần thử: {delivery_mode}."
    updated = owned_claim.update(**result, status=status, delivered_at=now if status == Reminder.Status.SENT else None,
        next_attempt_at=now + timedelta(minutes=1), title=title, message=message, last_error=error)
    return updated == 1 and status == Reminder.Status.SENT


def recover_stale_claims(*, now=None):
    now = now or timezone.now()
    stale = Reminder.objects.filter(status=Reminder.Status.SENDING, claimed_at__lte=now - timedelta(minutes=5))
    stale.filter(channel=Reminder.Channel.IN_APP).update(status=Reminder.Status.PENDING, claim_token=None, claimed_at=None)
    stale.filter(channel=Reminder.Channel.EMAIL).update(status=Reminder.Status.UNCERTAIN, claim_token=None,
        claimed_at=None, last_error="Worker bị gián đoạn khi gửi; chưa xác nhận email. Kiểm tra hộp thư trước khi gửi lại.")


def run_cycle(*, now=None):
    cycle_start = now or timezone.now()
    recover_stale_claims(now=cycle_start)
    created = enqueue_due_reminders(now=cycle_start)
    pending = Reminder.objects.filter(status__in=[Reminder.Status.PENDING, Reminder.Status.FAILED],
        next_attempt_at__lte=cycle_start, attempts__lt=MAX_ATTEMPTS).order_by("next_attempt_at", "pk")
    delivered = sum(dispatch_one(pk, now=now) for pk in list(pending.values_list("pk", flat=True)))
    return {"created": created, "delivered": delivered}
