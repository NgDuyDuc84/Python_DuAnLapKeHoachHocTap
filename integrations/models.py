import uuid

from django.conf import settings
from django.db import models


def event_id():
    return "nh" + uuid.uuid4().hex


class CalendarConnection(models.Model):
    class CalendarState(models.TextChoices):
        EMPTY = "empty", "Chưa tạo lịch"
        CREATING = "creating", "Đang tạo lịch"
        READY = "ready", "Đã có lịch"
        UNCERTAIN = "uncertain", "Chưa xác nhận tạo lịch"

    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    google_sub = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    encrypted_credentials = models.TextField(blank=True)
    is_connected = models.BooleanField(default=False)
    generation = models.UUIDField(default=uuid.uuid4)
    calendar_id = models.CharField(max_length=1024, blank=True)
    calendar_state = models.CharField(
        max_length=12, choices=CalendarState.choices, default=CalendarState.EMPTY,
    )
    last_error = models.CharField(max_length=32, blank=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)


class CalendarEventMapping(models.Model):
    connection = models.ForeignKey(CalendarConnection, on_delete=models.CASCADE)
    source_pk = models.PositiveBigIntegerField()
    study_session = models.ForeignKey(
        "planner.StudySession", on_delete=models.SET_NULL, null=True, blank=True,
    )
    week_start = models.DateField()
    event_id = models.CharField(max_length=64, default=event_id)
    title = models.CharField(max_length=250)
    remote_deleted = models.BooleanField(default=False)
    was_created = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["connection", "source_pk"], name="calendar_source_unique",
        )]


class CalendarSyncJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Đang chờ worker"
        RUNNING = "running", "Đang đồng bộ"
        SUCCESS = "success", "Đồng bộ thành công"
        FAILED = "failed", "Chưa hoàn tất"
        STALE = "stale", "Cần xem trước lại"

    connection = models.ForeignKey(CalendarConnection, on_delete=models.CASCADE)
    generation = models.UUIDField()
    week_start = models.DateField()
    input_hash = models.CharField(max_length=64)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    results = models.JSONField(default=dict)
    error = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    claim_token = models.UUIDField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [models.UniqueConstraint(
            fields=["connection"],
            condition=models.Q(status__in=["pending", "running"]),
            name="calendar_one_active_job",
        )]
