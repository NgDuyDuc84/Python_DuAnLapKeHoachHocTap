from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from focus.models import FocusSession, StudyLog
from insights.models import InsightReport
from integrations.models import CalendarConnection
from notifications.models import Reminder, ReminderPreference
from planner.models import BusyEvent, StudyPlan, StudyPreference, StudySession
from planner.services.availability import at_time
from studies.models import Material, Subject, Task


DEMO_SUBJECT = "[Demo] Lập trình Python"


class Command(BaseCommand):
    help = "Add synthetic study data to an existing empty, non-staff demo account. Never calls external services."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        user = get_user_model().objects.select_for_update().filter(username=options["username"]).first()
        if not user or not user.is_active or user.is_staff or user.is_superuser:
            raise CommandError("Use an existing active non-staff account dedicated to the demo.")
        if Subject.objects.filter(owner=user, name=DEMO_SUBJECT).exists():
            self.stdout.write("Demo already exists; no changes made.")
            return
        models = (Subject, Task, Material, BusyEvent, StudyPreference, StudyPlan, FocusSession,
                  StudyLog, Reminder, ReminderPreference, CalendarConnection, InsightReport)
        if any(model.objects.filter(owner=user).exists() for model in models):
            raise CommandError("The account is not empty; no changes made. Create a separate demo account.")
        today = timezone.localdate()
        first_day = today + timedelta(days=1)
        monday = first_day - timedelta(days=first_day.weekday())
        python = Subject.objects.create(owner=user, name=DEMO_SUBJECT, color="#176b58", semester="Học kỳ demo")
        database = Subject.objects.create(owner=user, name="[Demo] Cơ sở dữ liệu", color="#836339", semester="Học kỳ demo")
        tasks = []
        for subject, title, minutes, offset, priority, can_split, done in [
            (python, "[Demo] Hoàn thiện dự án Django", 180, 6, 3, True, False),
            (database, "[Demo] Ôn tập truy vấn SQL", 90, 3, 2, True, False),
            (python, "[Demo] Bài tập cần cập nhật tiến độ", 50, -1, 3, True, False),
            (database, "[Demo] Thực hành thiết kế dữ liệu", 80, 5, 2, False, False),
            (python, "[Demo] Ôn tập hàm Python", 50, 2, 1, True, True),
        ]:
            task = Task(owner=user, subject=subject, title=title, estimated_minutes=minutes,
                        remaining_minutes=0 if done else minutes, status="done" if done else "todo",
                        deadline=at_time(today + timedelta(days=offset), time(22)), priority=priority, can_split=can_split)
            task.full_clean()
            task.save()
            tasks.append(task)
        StudyPreference.objects.create(owner=user)
        BusyEvent.objects.create(owner=user, title="[Demo] Lịch lên lớp", starts_at=at_time(first_day, time(13)),
                                 ends_at=at_time(first_day, time(16)), repeat_weekly=True)
        plan = StudyPlan.objects.create(owner=user, week_start=monday, applied_at=timezone.now(), input_fingerprint="0" * 64)
        for task, hour, locked, status in [(tasks[0], 9, False, "planned"), (tasks[1], 10, True, "planned"), (tasks[3], 11, False, "cancelled")]:
            session = StudySession(owner=user, plan=plan, task=task, starts_at=at_time(first_day, time(hour)),
                                   ends_at=at_time(first_day, time(hour, 50)), is_locked=locked, status=status)
            session.full_clean()
            session.save()
        for offset, minutes in [(0, 25), (1, 50), (3, 30), (6, 45), (8, 25)]:
            StudyLog.objects.create(owner=user, task=tasks[0], task_title=tasks[0].title, subject_label=str(python),
                                    studied_on=today - timedelta(days=offset), minutes=minutes, notes="Dữ liệu minh họa.")
        Material.objects.create(owner=user, subject=python, task=tasks[0], title="[Demo] Django documentation", url="https://docs.djangoproject.com/en/5.2/")
        Material.objects.create(owner=user, subject=database, title="[Demo] PostgreSQL documentation", url="https://www.postgresql.org/docs/")
        ReminderPreference.objects.create(owner=user, in_app_enabled=True, email_enabled=False)
        self.stdout.write("Demo created: 2 subjects, 5 tasks, 2 materials, 3 sessions, 5 study logs (175 minutes).")
        self.stdout.write(f"Open the calendar week starting {monday.isoformat()}. Email reminders remain disabled.")
