from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone

DEADLINE_LEADS = [(60, "1 giờ trước hạn"), (180, "3 giờ trước hạn"), (1440, "24 giờ trước hạn")]
SESSION_LEADS = [(5, "5 phút trước buổi"), (15, "15 phút trước buổi"), (30, "30 phút trước buổi")]


class ReminderPreference(models.Model):
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    in_app_enabled = models.BooleanField("Nhận thông báo trong web", default=True)
    email_enabled = models.BooleanField("Nhận email nhắc", default=False)
    deadline_minutes = models.PositiveIntegerField("Nhắc deadline", choices=DEADLINE_LEADS, default=1440)
    session_minutes = models.PositiveIntegerField("Nhắc buổi học", choices=SESSION_LEADS, default=15)


class Reminder(models.Model):
    class Kind(models.TextChoices):
        DEADLINE = "deadline", "Deadline"
        SESSION = "session", "Buổi học"

    class Channel(models.TextChoices):
        IN_APP = "in_app", "Trong web"
        EMAIL = "email", "Email"

    class Status(models.TextChoices):
        PENDING = "pending", "Đang chờ"
        SENDING = "sending", "Đang xử lý"
        SENT = "sent", "Đã xử lý"
        FAILED = "failed", "Gửi lỗi"
        SKIPPED = "skipped", "Đã bỏ qua"
        UNCERTAIN = "uncertain", "Chưa xác nhận kết quả"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    task = models.ForeignKey("studies.Task", on_delete=models.SET_NULL, null=True, blank=True)
    study_session = models.ForeignKey("planner.StudySession", on_delete=models.SET_NULL, null=True, blank=True)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    channel = models.CharField(max_length=10, choices=Channel.choices)
    dedup_key = models.CharField(max_length=64)
    target_at = models.DateTimeField()
    remind_at = models.DateTimeField()
    title = models.CharField(max_length=240)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    attempts = models.PositiveSmallIntegerField(default=0)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    last_error = models.CharField(max_length=300, blank=True)
    claim_token = models.UUIDField(null=True, blank=True)
    claimed_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [models.UniqueConstraint(fields=["owner", "channel", "dedup_key"], name="reminder_event_channel_unique")]
        indexes = [models.Index(fields=["status", "next_attempt_at"], name="reminder_due_idx")]

    @property
    def target_url(self):
        if self.kind == self.Kind.DEADLINE and self.task_id:
            return reverse("studies:task_update", args=[self.task_id])
        if self.kind == self.Kind.SESSION and self.study_session_id:
            return reverse("planner:plan_detail", args=[self.study_session.plan_id])
        return ""

    @property
    def delivery_label(self):
        if self.status == self.Status.SENT:
            return "Đã hiển thị" if self.channel == self.Channel.IN_APP else "Đã bàn giao email"
        return self.get_status_display()

    @property
    def can_retry(self):
        return self.channel == self.Channel.EMAIL and self.status in (self.Status.FAILED, self.Status.UNCERTAIN)

    def clean(self):
        errors = {}
        for field in ("task", "study_session"):
            if getattr(self, f"{field}_id") and getattr(self, field).owner_id != self.owner_id:
                errors[field] = "Đối tượng được nhắc phải thuộc tài khoản của bạn."
        if self.study_session_id and self.task_id != self.study_session.task_id:
            errors["study_session"] = "Buổi học phải thuộc đúng công việc được nhắc."
        if errors:
            raise ValidationError(errors)
