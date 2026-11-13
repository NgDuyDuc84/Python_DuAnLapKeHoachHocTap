import hashlib
import json
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from planner.models import StudySession

from .google import GoogleCalendarClient, SyncError
from .models import CalendarConnection, CalendarEventMapping, CalendarSyncJob, event_id


def snapshot(connection, week):
    sessions = StudySession.objects.filter(
        owner=connection.owner, plan__owner=connection.owner,
        task__owner=connection.owner, plan__applied_at__isnull=False,
        plan__week_start=week,
    ).select_related("task__subject")
    desired = {}
    for session in sessions:
        if session.status == StudySession.Status.CANCELLED:
            continue
        title = session.task.title
        if session.status == StudySession.Status.DONE:
            title = "Đã học · " + title
        description = "Buổi học từ Nhịp Học. Nội dung/giờ được cập nhật theo ứng dụng."
        if session.task.subject_id:
            description += "\nMôn: " + session.task.subject.name
        description += "\n" + settings.SITE_URL + "/planner/"
        desired[session.pk] = {
            "summary": title,
            "description": description,
            "start": {"dateTime": timezone.localtime(session.starts_at).isoformat(), "timeZone": settings.TIME_ZONE},
            "end": {"dateTime": timezone.localtime(session.ends_at).isoformat(), "timeZone": settings.TIME_ZONE},
            "visibility": "private",
            "reminders": {"useDefault": False},
            "extendedProperties": {"private": {"nhiphoc": "study_session", "source": str(session.pk)}},
        }
    mappings = list(CalendarEventMapping.objects.filter(connection=connection, week_start=week))
    # Keep tombstones in the hash: completing our own deletes must not invalidate a job.
    orphans = sorted(m.source_pk for m in mappings if m.source_pk not in desired)
    digest = hashlib.sha256(json.dumps(
        {"desired": desired, "orphans": orphans}, sort_keys=True, ensure_ascii=False,
    ).encode()).hexdigest()
    return {
        "hash": digest, "desired": desired,
        "deletions": [m for m in mappings if m.source_pk not in desired and not m.remote_deleted],
    }


def queue_job(connection, week, input_hash):
    try:
        with transaction.atomic():
            return CalendarSyncJob.objects.create(
                connection=connection, generation=connection.generation,
                week_start=week, input_hash=input_hash,
            ), True
    except IntegrityError:
        return CalendarSyncJob.objects.filter(
            connection=connection, status__in=[CalendarSyncJob.Status.PENDING, CalendarSyncJob.Status.RUNNING],
        ).first(), False


def owns_event(event, source_pk):
    private = event.get("extendedProperties", {}).get("private", {})
    return private.get("nhiphoc") == "study_session" and private.get("source") == str(source_pk)


def run_job(job_id, *, client_class=None):
    now = timezone.now()
    token = uuid.uuid4()
    claimed = CalendarSyncJob.objects.filter(pk=job_id).filter(
        Q(status=CalendarSyncJob.Status.PENDING)
        | Q(status=CalendarSyncJob.Status.RUNNING, started_at__lt=now - timedelta(minutes=5))
    ).update(status=CalendarSyncJob.Status.RUNNING, started_at=now, claim_token=token)
    if not claimed:
        return False
    job = CalendarSyncJob.objects.select_related("connection__owner").get(pk=job_id)
    connection = job.connection
    counts = {"updated": 0, "deleted": 0}
    client = None

    def guard():
        if not CalendarSyncJob.objects.filter(
            pk=job.pk, claim_token=token, status=CalendarSyncJob.Status.RUNNING,
            connection__is_connected=True, connection__owner__is_active=True,
            connection__generation=job.generation,
        ).update(started_at=timezone.now()):
            raise SyncError("stale")
        if snapshot(connection, job.week_start)["hash"] != job.input_hash:
            raise SyncError("stale")

    def save_connection(**fields):
        guard()
        if not CalendarConnection.objects.filter(
            pk=connection.pk, is_connected=True, generation=job.generation,
        ).update(**fields):
            raise SyncError("stale")
        for key, value in fields.items():
            setattr(connection, key, value)

    try:
        guard()
        data = snapshot(connection, job.week_start)
        if not data["desired"] and not data["deletions"]:
            pass
        else:
            client = (client_class or GoogleCalendarClient)(connection)
            state = CalendarConnection.CalendarState
            if connection.calendar_state in (state.CREATING, state.UNCERTAIN):
                save_connection(calendar_state=state.UNCERTAIN)
                raise SyncError("calendar_uncertain")
            if connection.calendar_state == state.EMPTY:
                save_connection(calendar_state=state.CREATING)
                try:
                    result = client.create_calendar()
                    if not result or not result.get("id"):
                        raise SyncError("calendar_uncertain")
                except SyncError:
                    save_connection(calendar_state=state.UNCERTAIN)
                    raise SyncError("calendar_uncertain") from None
                save_connection(calendar_id=result["id"], calendar_state=state.READY)
            guard()
            if not client.calendar(connection.calendar_id):
                raise SyncError("calendar_missing")
            for source_pk, payload in data["desired"].items():
                guard()
                mapping, _ = CalendarEventMapping.objects.get_or_create(
                    connection=connection, source_pk=source_pk,
                    defaults={"study_session_id": source_pk, "week_start": job.week_start, "title": payload["summary"]},
                )
                existing = client.event(connection.calendar_id, mapping.event_id)
                guard()
                if existing and existing.get("status") != "cancelled" and not owns_event(existing, source_pk):
                    raise SyncError("event_owner")
                if mapping.remote_deleted or (existing and existing.get("status") == "cancelled") or (not existing and mapping.was_created):
                    mapping.event_id = event_id()
                    mapping.was_created = False
                    mapping.remote_deleted = False
                    mapping.save(update_fields=["event_id", "was_created", "remote_deleted"])
                    existing = None
                guard()
                result = client.upsert(connection.calendar_id, mapping.event_id, payload, exists=bool(existing))
                if result and result.get("conflict"):
                    guard()
                    existing = client.event(connection.calendar_id, mapping.event_id)
                    if not existing or not owns_event(existing, source_pk):
                        raise SyncError("event_owner")
                    guard()
                    result = client.upsert(connection.calendar_id, mapping.event_id, payload, exists=True)
                if not result or result.get("id") != mapping.event_id:
                    raise SyncError("provider")
                guard()
                mapping.was_created = True
                mapping.title = payload["summary"]
                mapping.save(update_fields=["was_created", "title"])
                counts["updated"] += 1
            for mapping in data["deletions"]:
                guard()
                existing = client.event(connection.calendar_id, mapping.event_id)
                if existing and existing.get("status") != "cancelled":
                    if not owns_event(existing, mapping.source_pk):
                        raise SyncError("event_owner")
                    guard()
                    client.delete(connection.calendar_id, mapping.event_id)
                guard()
                mapping.remote_deleted = True
                mapping.save(update_fields=["remote_deleted"])
                counts["deleted"] += 1
        save_connection(last_sync_at=timezone.now(), last_error="")
        status, error = CalendarSyncJob.Status.SUCCESS, ""
    except SyncError as exc:
        status = CalendarSyncJob.Status.STALE if exc.code == "stale" else CalendarSyncJob.Status.FAILED
        error = exc.code
        CalendarConnection.objects.filter(pk=connection.pk, generation=job.generation).update(last_error=error)
    finally:
        if client:
            client.close()
    CalendarSyncJob.objects.filter(pk=job.pk, claim_token=token, status=CalendarSyncJob.Status.RUNNING).update(
        status=status, error=error, results=counts, finished_at=timezone.now(), claim_token=None,
    )
    return True


def run_cycle():
    cutoff = timezone.now() - timedelta(minutes=5)
    ids = CalendarSyncJob.objects.filter(
        Q(status=CalendarSyncJob.Status.PENDING)
        | Q(status=CalendarSyncJob.Status.RUNNING, started_at__lt=cutoff)
    ).order_by("created_at").values_list("pk", flat=True)
    return sum(run_job(pk) for pk in list(ids))
