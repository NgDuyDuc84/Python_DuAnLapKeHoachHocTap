from django.conf import settings
from django.db import models


class InsightReport(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", "Đang phân tích"
        SUCCESS = "success", "Đã có kết quả AI"
        FAILED = "failed", "Chưa có kết quả AI"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    request_key = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    model_name = models.CharField(max_length=100)
    input_hash = models.CharField(max_length=64)
    snapshot = models.JSONField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.RUNNING)
    result = models.JSONField(default=dict)
    error = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "request_key"], name="insight_request_unique"),
            models.UniqueConstraint(fields=["owner"], condition=models.Q(status="running"), name="insight_one_running"),
        ]
