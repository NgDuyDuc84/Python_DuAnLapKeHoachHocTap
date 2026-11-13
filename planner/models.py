from datetime import time, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

DAY_CHOICES = [
    (0, "Thứ Hai"), (1, "Thứ Ba"), (2, "Thứ Tư"), (3, "Thứ Năm"),
    (4, "Thứ Sáu"), (5, "Thứ Bảy"), (6, "Chủ nhật"),
]


def default_study_days():
    return list(range(7))


def validate_study_days(value):
    if (
        not isinstance(value, list)
        or any(type(day) is not int or day not in range(7) for day in value)
        or len(set(value)) != len(value)
    ):
        raise ValidationError("Chọn các ngày hợp lệ trong tuần, không trùng nhau.")


class StudyPreference(models.Model):
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    study_days = models.JSONField(
        "Ngày được học", default=default_study_days, blank=True,
        validators=[validate_study_days],
    )
    study_start = models.TimeField("Bắt đầu khung học", default=time(8))
    study_end = models.TimeField("Kết thúc khung học", default=time(22))
    max_daily_minutes = models.PositiveIntegerField(
        "Tối đa phút học mỗi ngày", default=240,
        validators=[MinValueValidator(1), MaxValueValidator(1440)],
    )
    session_minutes = models.PositiveIntegerField(
        "Độ dài buổi học mong muốn (phút)", default=50,
        validators=[MinValueValidator(1), MaxValueValidator(1440)],
    )
    break_minutes = models.PositiveIntegerField(
        "Nghỉ giữa các buổi học (phút)", default=10,
        validators=[MaxValueValidator(1440)],
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(study_end__gt=models.F("study_start")),
                name="preference_window_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(max_daily_minutes__gte=1, max_daily_minutes__lte=1440),
                name="preference_daily_limit_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(session_minutes__gte=1, session_minutes__lte=models.F("max_daily_minutes")),
                name="preference_session_limit_valid",
            ),
        ]

    def clean(self):
        errors = {}
        if self.study_start and self.study_end:
            if self.study_end <= self.study_start:
                errors["study_end"] = "Khung học phải kết thúc sau giờ bắt đầu, trong cùng ngày."
            elif self.session_minutes is not None:
                window = (self.study_end.hour * 60 + self.study_end.minute
                          - self.study_start.hour * 60 - self.study_start.minute)
                if self.session_minutes > window:
                    errors["session_minutes"] = "Độ dài buổi học không được vượt khung giờ học."
        if self.session_minutes is not None and self.max_daily_minutes is not None:
            if self.session_minutes > self.max_daily_minutes:
                errors["session_minutes"] = "Độ dài buổi học không được vượt giới hạn mỗi ngày."
        if errors:
            raise ValidationError(errors)


class BusyEvent(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField("Tên lịch bận", max_length=200)
    starts_at = models.DateTimeField("Bắt đầu")
    ends_at = models.DateTimeField("Kết thúc")
    repeat_weekly = models.BooleanField("Lặp hằng tuần", default=False)
    repeat_until = models.DateField("Ngày kết thúc chuỗi lặp", null=True, blank=True)

    class Meta:
        ordering = ["starts_at", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(ends_at__gt=models.F("starts_at")),
                name="busy_event_time_valid",
            ),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        errors = {}
        if self.starts_at and self.ends_at:
            if self.ends_at <= self.starts_at:
                errors["ends_at"] = "Thời điểm kết thúc phải sau thời điểm bắt đầu."
            elif self.repeat_weekly and self.ends_at - self.starts_at >= timedelta(days=7):
                errors["ends_at"] = "Một lần của lịch lặp phải ngắn hơn 7 ngày."
        if self.repeat_until:
            if not self.repeat_weekly:
                errors["repeat_until"] = "Ngày kết thúc chuỗi chỉ dùng cho lịch lặp hằng tuần."
            elif self.starts_at and self.repeat_until < timezone.localtime(self.starts_at).date():
                errors["repeat_until"] = "Ngày kết thúc chuỗi không được trước ngày bắt đầu."
        if errors:
            raise ValidationError(errors)


class StudyPlan(models.Model):
    class Mode(models.TextChoices):
        ADD = "add", "Bổ sung, giữ mọi buổi đã áp dụng"
        REPLACE = "replace", "Xếp lại buổi tự động chưa bắt đầu trong tuần"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    week_start = models.DateField("Thứ Hai đầu tuần")
    created_at = models.DateTimeField(auto_now_add=True)
    applied_at = models.DateTimeField("Đã áp dụng lúc", null=True, blank=True)
    input_fingerprint = models.CharField(max_length=64)
    report = models.JSONField(default=list, blank=True)
    mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.ADD)
    replacement_ids = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    @property
    def week_end(self):
        return self.week_start + timedelta(days=6)

    def clean(self):
        if self.week_start and self.week_start.weekday() != 0:
            raise ValidationError({"week_start": "Tuần phải bắt đầu vào thứ Hai."})


class StudySession(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", "Chưa ghi nhận"
        DONE = "done", "Đã học"
        CANCELLED = "cancelled", "Đã hủy / bỏ qua"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE, related_name="sessions")
    task = models.ForeignKey("studies.Task", on_delete=models.CASCADE, related_name="study_sessions")
    starts_at = models.DateTimeField("Bắt đầu")
    ends_at = models.DateTimeField("Kết thúc")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PLANNED)
    is_locked = models.BooleanField("Giữ buổi khi xếp lại", default=False)
    is_manual = models.BooleanField("Đã chỉnh tay", default=False)

    class Meta:
        ordering = ["starts_at", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(ends_at__gt=models.F("starts_at")),
                name="study_session_time_valid",
            ),
        ]

    @property
    def duration_minutes(self):
        return int((self.ends_at - self.starts_at).total_seconds() // 60)

    def clean(self):
        errors = {}
        for name in ("plan", "task"):
            if getattr(self, f"{name}_id") and getattr(self, name).owner_id != self.owner_id:
                errors[name] = "Chỉ được dùng dữ liệu thuộc tài khoản của bạn."
        if self.starts_at and self.ends_at:
            start, end = timezone.localtime(self.starts_at), timezone.localtime(self.ends_at)
            if end <= start or start.date() != end.date():
                errors["ends_at"] = "Buổi học phải kết thúc sau bắt đầu, trong cùng ngày."
            if self.task_id and end > self.task.deadline:
                errors["ends_at"] = "Buổi học không được vượt deadline."
            if self.plan_id and not self.plan.week_start <= start.date() <= self.plan.week_end:
                errors["starts_at"] = "Buổi học phải thuộc tuần của kế hoạch."
        if errors:
            raise ValidationError(errors)
