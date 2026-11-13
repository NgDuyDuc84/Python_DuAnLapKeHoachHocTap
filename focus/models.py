import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class FocusSession(models.Model):
    class Phase(models.TextChoices):
        WORK = "work", "Học tập"
        BREAK = "break", "Nghỉ ngắn"

    class Status(models.TextChoices):
        RUNNING = "running", "Đang chạy"
        PAUSED = "paused", "Tạm dừng"
        FINISHED = "finished", "Đã kết thúc"
        CANCELLED = "cancelled", "Đã hủy"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    task = models.ForeignKey("studies.Task", on_delete=models.SET_NULL, null=True, blank=True)
    task_title = models.CharField(max_length=200)
    subject_label = models.CharField(max_length=210, blank=True)
    request_key = models.UUIDField(default=uuid.uuid4)
    previous_work = models.OneToOneField("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="rest_session")
    phase = models.CharField(max_length=8, choices=Phase.choices, default=Phase.WORK)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.RUNNING)
    duration_seconds = models.PositiveIntegerField(default=25 * 60)
    elapsed_seconds = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(default=timezone.now)
    resumed_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at", "-pk"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "request_key"], name="focus_request_unique"),
            models.UniqueConstraint(fields=["owner"], condition=models.Q(status__in=["running", "paused"]), name="focus_one_active_per_owner"),
            models.CheckConstraint(condition=models.Q(duration_seconds__gt=0, elapsed_seconds__lte=models.F("duration_seconds")), name="focus_duration_valid"),
            models.CheckConstraint(condition=(
                models.Q(status="running", resumed_at__isnull=False, finished_at__isnull=True)
                | models.Q(status="paused", resumed_at__isnull=True, finished_at__isnull=True)
                | models.Q(status__in=["finished", "cancelled"], resumed_at__isnull=True, finished_at__isnull=False)
            ), name="focus_state_valid"),
        ]

    @property
    def is_active(self):
        return self.status in (self.Status.RUNNING, self.Status.PAUSED)

    def elapsed(self, now=None):
        extra = 0
        if self.status == self.Status.RUNNING:
            extra = max(0, int(((now or timezone.now()) - self.resumed_at).total_seconds()))
        return min(self.duration_seconds, self.elapsed_seconds + extra)

    def clean(self):
        errors = {}
        if self.task_id and self.task.owner_id != self.owner_id:
            errors["task"] = "Công việc phải thuộc tài khoản của bạn."
        if self.previous_work_id:
            if (self.previous_work.owner_id != self.owner_id
                    or self.previous_work.phase != self.Phase.WORK or self.phase != self.Phase.BREAK):
                errors["previous_work"] = "Giờ nghỉ phải liên kết với phiên học của chính bạn."
        if errors:
            raise ValidationError(errors)


class StudyLog(models.Model):
    class Source(models.TextChoices):
        MANUAL = "manual", "Nhập tay"
        POMODORO = "pomodoro", "Pomodoro"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    task = models.ForeignKey("studies.Task", on_delete=models.SET_NULL, null=True, blank=True)
    task_title = models.CharField(max_length=200)
    subject_label = models.CharField(max_length=210, blank=True)
    studied_on = models.DateField("Ngày học", default=timezone.localdate)
    minutes = models.PositiveIntegerField("Số phút đã học", validators=[MinValueValidator(1), MaxValueValidator(1440)])
    notes = models.TextField("Ghi chú", blank=True, max_length=1000)
    source = models.CharField(max_length=10, choices=Source.choices, default=Source.MANUAL)
    focus_session = models.OneToOneField(FocusSession, on_delete=models.SET_NULL, null=True, blank=True, related_name="study_log")
    entry_key = models.UUIDField(default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-studied_on", "-pk"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "entry_key"], name="study_log_request_unique"),
            models.CheckConstraint(condition=models.Q(minutes__gte=1, minutes__lte=1440), name="study_log_minutes_valid"),
        ]

    def __str__(self):
        return f"{self.task_title} — {self.minutes} phút"

    def clean(self):
        errors = {}
        if self.task_id and self.task.owner_id != self.owner_id:
            errors["task"] = "Chỉ được ghi công việc thuộc tài khoản của bạn."
        if self.focus_session_id and self.focus_session.owner_id != self.owner_id:
            errors["focus_session"] = "Phiên tập trung phải thuộc tài khoản của bạn."
        if self.studied_on and self.studied_on > timezone.localdate():
            errors["studied_on"] = "Không ghi nhật ký cho ngày tương lai."
        if errors:
            raise ValidationError(errors)
