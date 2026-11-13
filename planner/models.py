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
