from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from focus.models import FocusSession, StudyLog
from insights.models import InsightReport
from integrations.models import CalendarConnection
from notifications.models import Reminder, ReminderPreference
from notifications.services import reminder_text
from planner.models import BusyEvent, StudyPlan, StudyPreference, StudySession
from planner.services.availability import at_time
from studies.models import Material, Subject, Task


DEMO_SUBJECT = "[Demo] Lập trình Python"


class Command(BaseCommand):
    help = "Add realistic synthetic study data to an existing empty, non-staff account. Never calls external services."

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
        subjects = []
        for name, color in [(DEMO_SUBJECT, "#1D6B56"), ("Cơ sở dữ liệu", "#24507F"),
                            ("Cấu trúc dữ liệu và giải thuật", "#8A5410"), ("Mạng máy tính", "#9C2F26")]:
            subjects.append(Subject.objects.create(owner=user, name=name, color=color, semester="Học kỳ 1"))
        tasks = []
        for subject, title, estimate, remaining, offset, priority in [
            (0, "Hoàn thiện chức năng đăng nhập cho đồ án Django", 180, 120, 6, 3),
            (1, "Luyện JOIN và truy vấn thống kê điểm sinh viên", 150, 100, 3, 3),
            (3, "Nộp bài thực hành chia subnet", 60, 60, -1, 3),
            (1, "Vẽ ERD hệ thống quản lý thư viện", 100, 50, 5, 2),
            (0, "Bài tập hàm, list và dictionary", 50, 0, -1, 1),
            (2, "Cài đặt tìm kiếm nhị phân và viết test", 90, 90, 4, 2),
            (1, "Ôn chuẩn hóa dữ liệu đến dạng chuẩn 3NF", 120, 120, 8, 2),
            (3, "Tóm tắt mô hình TCP/IP", 75, 0, -3, 1),
            (2, "Chuẩn bị thuyết trình độ phức tạp thuật toán", 90, 90, 2, 3),
            (0, "Viết kiểm thử cho module quản lý công việc", 120, 120, 7, 2),
            (2, "Tổng hợp kiến thức stack và queue", 45, 0, -1, 1),
            (3, "Thực hành socket client/server bằng Python", 90, 90, 10, 2),
        ]:
            task = Task(owner=user, subject=subjects[subject], title=title,
                        description="Bài tập học kỳ; ghi lại kết quả và câu hỏi cần trao đổi trên lớp.",
                        estimated_minutes=estimate, remaining_minutes=remaining,
                        status="done" if remaining == 0 else "in_progress" if remaining < estimate else "todo",
                        deadline=at_time(today + timedelta(days=offset), time(22)), priority=priority)
            task.full_clean()
            task.save()
            tasks.append(task)
        StudyPreference.objects.create(owner=user)
        for offset, title in [(1, "Lên lớp: thực hành tại phòng máy"), (2, "Lên lớp: cơ sở dữ liệu")]:
            day = today + timedelta(days=offset)
            BusyEvent.objects.create(owner=user, title=title, starts_at=at_time(day, time(13)),
                                     ends_at=at_time(day, time(16)), repeat_weekly=True)
        BusyEvent.objects.create(owner=user, title="Họp nhóm đồ án tại thư viện",
                                 starts_at=at_time(today + timedelta(days=1), time(17)),
                                 ends_at=at_time(today + timedelta(days=1), time(18)))
        plans = {}
        sessions = []
        for offset, hour, task_index, status, locked, manual in [
            (-3, 8, 7, "done", False, False), (-2, 9, 4, "done", False, False),
            (-1, 18, 10, "done", False, False), (0, 8, 0, "planned", False, False),
            (1, 9, 0, "planned", False, False), (1, 10, 1, "planned", True, False),
            (2, 19, 5, "planned", False, True), (3, 9, 3, "planned", False, False),
            (4, 19, 9, "planned", False, False), (5, 10, 11, "cancelled", False, False),
        ]:
            day = today + timedelta(days=offset)
            monday = day - timedelta(days=day.weekday())
            if monday not in plans:
                plans[monday] = StudyPlan.objects.create(owner=user, week_start=monday,
                    applied_at=at_time(monday, time(7)), input_fingerprint="0" * 64)
            duration = 45 if task_index == 10 else 50
            session = StudySession(owner=user, plan=plans[monday], task=tasks[task_index],
                starts_at=at_time(day, time(hour)), ends_at=at_time(day, time(hour)) + timedelta(minutes=duration),
                status=status, is_locked=locked, is_manual=manual)
            session.full_clean()
            session.save()
            sessions.append(session)
        for offset, minutes in enumerate([25, 50, 40, 25, 60, 45, 50, 30, 25, 45, 50, 30, 60, 25]):
            day = today - timedelta(days=offset)
            task = tasks[[0, 1, 5, 7][offset % 4]]
            focus = None
            if offset in (3, 8, 13):
                focus = FocusSession.objects.create(owner=user, task=task, task_title=task.title,
                    subject_label=str(task.subject), status="finished", elapsed_seconds=1500,
                    started_at=at_time(day, time(8)), finished_at=at_time(day, time(8, 25)))
            StudyLog.objects.create(owner=user, task=task, task_title=task.title, subject_label=str(task.subject),
                studied_on=day, minutes=minutes, notes="Đã luyện bài tập và ghi lại các ý chưa nắm chắc.",
                source="pomodoro" if focus else "manual", focus_session=focus)
        for subject, task_index, title, url in [
            (0, 0, "Django: xác thực người dùng", "https://docs.djangoproject.com/en/5.2/topics/auth/"),
            (0, 4, "Python: cấu trúc dữ liệu", "https://docs.python.org/3/tutorial/datastructures.html"),
            (0, 9, "Django: kiểm thử ứng dụng", "https://docs.djangoproject.com/en/5.2/topics/testing/"),
            (1, 1, "PostgreSQL: bảng và truy vấn JOIN", "https://www.postgresql.org/docs/current/tutorial-join.html"),
            (1, 6, "PostgreSQL: ràng buộc dữ liệu", "https://www.postgresql.org/docs/current/ddl-constraints.html"),
            (2, 5, "Python: tìm kiếm nhị phân với bisect", "https://docs.python.org/3/library/bisect.html"),
            (2, 10, "Python: hàng đợi với deque", "https://docs.python.org/3/library/collections.html#collections.deque"),
            (3, 11, "Python: lập trình socket", "https://docs.python.org/3/library/socket.html"),
        ]:
            Material.objects.create(owner=user, subject=subjects[subject], task=tasks[task_index], title=title, url=url)
        ReminderPreference.objects.create(owner=user, in_app_enabled=True, email_enabled=False)
        for index, session in enumerate(sessions[:3]):
            delivered = session.starts_at - timedelta(minutes=15)
            title, message = reminder_text(Reminder.Kind.SESSION, session.task, session.starts_at)
            Reminder.objects.create(owner=user, task=session.task, study_session=session, kind="session", channel="in_app",
                dedup_key=f"demo-session-{session.pk}", target_at=session.starts_at, remind_at=delivered,
                title=title, message=message, status="sent", delivered_at=delivered,
                read_at=delivered + timedelta(hours=1) if index == 0 else None)
        self.stdout.write("Demo created: 4 subjects, 12 tasks, 8 materials, 10 sessions, 14 study logs (560 minutes), 3 notifications.")
        self.stdout.write(f"Open the calendar week starting {(today - timedelta(days=today.weekday())).isoformat()}. Email reminders remain disabled.")
