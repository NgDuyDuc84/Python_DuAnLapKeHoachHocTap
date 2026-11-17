from datetime import datetime, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase

from .dashboard import select_dashboard_action


class DashboardActionTests(SimpleTestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 17, 9, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
        self.task = SimpleNamespace(pk=11, title="Học Python", deadline=self.now + timedelta(days=3))
        self.ongoing = self.session(21, -10, 40)
        self.past = self.session(22, -60, -10)
        self.upcoming = self.session(23, 60, 110)
        self.overdue = {"task": SimpleNamespace(pk=12, title="Bài quá hạn", deadline=self.now - timedelta(days=1)),
                        "overdue": True, "missing": 30}
        self.shortfall = {"task": self.task, "overdue": False, "missing": 30}
        self.focus = SimpleNamespace(pk=31, task_title="Phiên hiện tại")
        self.data = {"now": self.now, "active_focus": None, "sessions": [], "unrecorded": None,
                     "task_alerts": [], "has_subjects": True, "has_tasks": True, "has_plan": True}

    def session(self, pk, start, end, status="planned"):
        return SimpleNamespace(pk=pk, task=self.task, task_id=self.task.pk, status=status,
                               starts_at=self.now + timedelta(minutes=start), ends_at=self.now + timedelta(minutes=end))

    def test_all_eight_branches_return_content_and_at_most_two_actions(self):
        cases = (
            ("focus", {"active_focus": self.focus}, "Tiếp tục"),
            ("ongoing", {"sessions": [self.ongoing]}, "Bắt đầu tập trung"),
            ("unrecorded", {"unrecorded": self.past}, "Ghi nhận buổi này"),
            ("overdue", {"task_alerts": [self.overdue]}, "Cập nhật tiến độ"),
            ("shortfall", {"task_alerts": [self.shortfall]}, "Xếp lịch"),
            ("upcoming", {"sessions": [self.upcoming]}, "Xem lịch"),
            ("onboarding", {"has_tasks": False, "has_subjects": False, "has_plan": False}, None),
            ("ready", {}, "Bắt đầu tập trung"),
        )
        for kind, changes, label in cases:
            with self.subTest(kind=kind):
                data = {**self.data, **changes}
                result = select_dashboard_action(**data)
                self.assertEqual(result["kind"], kind)
                self.assertTrue(result["title"])
                self.assertEqual(result["primary"]["label"] if result["primary"] else None, label)
                self.assertLessEqual(sum(result[key] is not None for key in ("primary", "secondary")), 2)
                self.assertEqual(result, select_dashboard_action(**data))

    def test_priority_is_a_through_h_when_multiple_conditions_match(self):
        data = {**self.data, "active_focus": self.focus, "sessions": [self.ongoing, self.upcoming],
                "unrecorded": self.past, "task_alerts": [self.overdue, self.shortfall], "has_plan": False}
        for expected, change in (
            ("focus", {}), ("ongoing", {"active_focus": None}),
            ("unrecorded", {"sessions": [self.upcoming]}), ("overdue", {"unrecorded": None}),
            ("shortfall", {"task_alerts": [self.shortfall]}), ("upcoming", {"task_alerts": []}),
            ("onboarding", {"sessions": []}), ("ready", {"has_plan": True}),
        ):
            with self.subTest(expected=expected):
                data.update(change)
                self.assertEqual(select_dashboard_action(**data)["kind"], expected)

    def test_start_actions_target_existing_post_endpoint_and_correct_task(self):
        for data, key in (({"sessions": [self.ongoing]}, "primary"),
                          ({"task_alerts": [self.shortfall]}, "secondary")):
            action = select_dashboard_action(**{**self.data, **data})[key]
            self.assertEqual((action["method"], action["url"], action["task_id"]), ("post", "focus:home", 11))
        ready = select_dashboard_action(**self.data)["primary"]
        self.assertEqual(ready["method"], "get")

    def test_future_day_finished_or_cancelled_session_is_not_today_next_action(self):
        for session in (self.session(40, 24 * 60, 25 * 60), self.session(41, 10, 50, "done"),
                        self.session(42, -10, 20, "cancelled")):
            with self.subTest(session=session.pk):
                result = select_dashboard_action(**{**self.data, "sessions": [session]})
                self.assertEqual(result["kind"], "ready")

    def test_each_unfinished_onboarding_step_keeps_checklist(self):
        for key in ("has_subjects", "has_tasks", "has_plan"):
            with self.subTest(key=key):
                self.assertEqual(select_dashboard_action(**{**self.data, key: False})["kind"], "onboarding")

    def test_session_and_deadline_boundaries(self):
        start_now = self.session(50, 0, 30)
        self.assertEqual(select_dashboard_action(**{**self.data, "sessions": [start_now]})["kind"], "ongoing")
        end_now = self.session(51, -30, 0)
        self.assertEqual(select_dashboard_action(**{**self.data, "sessions": [end_now], "unrecorded": end_now})["kind"], "unrecorded")
        self.task.deadline = self.now + timedelta(days=7, seconds=1)
        self.assertEqual(select_dashboard_action(**{**self.data, "task_alerts": [self.shortfall]})["kind"], "ready")
