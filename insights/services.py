from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone

from . import provider
from .data import fingerprint
from .models import InsightReport
from .provider import InsightError, ProviderError


def generate_report(user, snapshot, request_key):
    now = timezone.now()
    try:
        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=user.pk, is_active=True)
            previous = InsightReport.objects.filter(owner=user, request_key=request_key).first()
            if previous:
                return previous
            InsightReport.objects.filter(owner=user, status="running", created_at__lt=now - timedelta(minutes=5)).update(
                status="failed", error="interrupted", finished_at=now,
            )
            if InsightReport.objects.filter(owner=user, status="running").exists():
                raise InsightError("Bạn đang có yêu cầu AI đang xử lý. Hãy chờ kết quả.")
            if not provider.configured():
                raise ProviderError("configuration")
            if InsightReport.objects.filter(owner=user, created_at__gte=now - timedelta(seconds=60)).exists():
                raise InsightError("Vui lòng chờ đủ 60 giây giữa hai yêu cầu AI.")
            if InsightReport.objects.filter(owner=user, created_at__date=timezone.localdate(now)).count() >= 5:
                raise InsightError("Bạn đã dùng 5 yêu cầu AI trong ngày. Có thể tiếp tục dùng phân tích Python.")
            report = InsightReport.objects.create(
                owner=user, request_key=request_key, model_name=settings.GROQ_MODEL,
                input_hash=fingerprint(snapshot), snapshot=snapshot,
            )
    except IntegrityError:
        previous = InsightReport.objects.filter(owner=user, request_key=request_key).first()
        if previous:
            return previous
        raise InsightError("Một yêu cầu khác vừa được tạo. Hãy tải lại lịch sử AI.") from None
    try:
        result = provider.analyze(snapshot["payload"])
        status, error = InsightReport.Status.SUCCESS, ""
    except ProviderError as exc:
        result, status, error = {}, InsightReport.Status.FAILED, exc.code
    # A late response cannot replace a request already marked interrupted.
    InsightReport.objects.filter(pk=report.pk, status="running").update(
        result=result, status=status, error=error, finished_at=timezone.now(),
    )
    report.refresh_from_db()
    return report
