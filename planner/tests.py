from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse

from studies.models import Task

from .models import BusyEvent, StudyPreference
from .services.availability import (
    at_time, available_intervals, build_week, expand_busy_events, subtract_busy,
)

User = get_user_model()


def moment(day, hour=0, minute=0):
    return at_time(date(2026, 11, day), time(hour, minute))


class CalendarMathTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(username="calendar_math")

    def event(self, start, end, **extra):
        return BusyEvent.objects.create(
            owner=self.owner, title="Busy interval", starts_at=start, ends_at=end, **extra
        )

    def test_busy_subtraction_merges_overlap_duplicates_and_adjacent_intervals(self):
        cases = [
            ([], [(moment(16, 8), moment(16, 12))]),
            ([(moment(16, 7), moment(16, 9)), (moment(16, 8), moment(16, 10)),
              (moment(16, 10), moment(16, 11))], [(moment(16, 11), moment(16, 12))]),
            ([(moment(16, 8), moment(16, 9))] * 2, [(moment(16, 9), moment(16, 12))]),
            ([(moment(16, 7), moment(16, 8)), (moment(16, 12), moment(16, 13))],
             [(moment(16, 8), moment(16, 12))]),
            ([(moment(16, 7), moment(16, 13))], []),
        ]
        for blocked, expected in cases:
            with self.subTest(blocked=blocked):
                self.assertEqual(subtract_busy(moment(16, 8), moment(16, 12), blocked), expected)

    def test_one_time_events_use_half_open_week_boundaries(self):
        inside = self.event(moment(17, 10), moment(17, 12))
        before = self.event(moment(15, 22), moment(16))
        after = self.event(moment(23), moment(23, 1))
        result = expand_busy_events([before, after, inside], moment(16), moment(23))
        self.assertEqual([item.event for item in result], [inside])

    def test_weekly_occurrences_keep_local_clock_and_stop_inclusively(self):
        event = self.event(moment(2, 9), moment(2, 11), repeat_weekly=True, repeat_until=date(2026, 11, 23))
        for start, end, expected in ((16, 23, 16), (23, 30, 23)):
            result = expand_busy_events([event], moment(start), moment(end))
            self.assertEqual(len(result), 1)
            self.assertEqual((result[0].starts_at, result[0].ends_at),
                             (moment(expected, 9), moment(expected, 11)))
        self.assertEqual(expand_busy_events([event], moment(30), moment(30) + timedelta(days=7)), [])

    def test_recurring_event_does_not_start_before_anchor(self):
        event = self.event(moment(23, 9), moment(23, 11), repeat_weekly=True)
        self.assertEqual(expand_busy_events([event], moment(16), moment(23)), [])

    def test_overnight_recurrence_includes_previous_week_and_clips_calendar_days(self):
        event = self.event(moment(8, 22), moment(9, 2), repeat_weekly=True)
        result = expand_busy_events([event], moment(16), moment(23))
        self.assertEqual([item.starts_at for item in result], [moment(15, 22), moment(22, 22)])
        days = build_week(self.owner, date(2026, 11, 16), StudyPreference(owner=self.owner), now=moment(15))
        self.assertEqual(days[0]["items"][0]["start_label"], "00:00")
        self.assertEqual(days[0]["items"][0]["end_label"], "02:00")
        self.assertEqual(days[-1]["items"][0]["end_label"], "24:00")

    def test_multiday_one_time_busy_blocks_each_day_correctly(self):
        self.event(moment(15, 20), moment(17, 2))
        days = build_week(self.owner, date(2026, 11, 16), StudyPreference(owner=self.owner), now=moment(15))
        self.assertEqual(days[0]["free"], [])
        self.assertEqual(days[0]["items"][0]["end_label"], "24:00")
        self.assertEqual(days[1]["items"][0]["end_label"], "02:00")
        self.assertEqual(days[1]["free"][0]["start_label"], "08:00")

    def test_selected_days_and_current_time_limit_available_intervals(self):
        preference = StudyPreference(owner=self.owner, study_days=[0], study_start=time(8), study_end=time(12))
        self.assertEqual(available_intervals(date(2026, 11, 17), preference, [], moment(15)), [])
        self.assertEqual(available_intervals(date(2026, 11, 16), preference, [], moment(17)), [])
        now = moment(16, 9) + timedelta(seconds=1)
        self.assertEqual(available_intervals(date(2026, 11, 16), preference, [], now),
                         [(moment(16, 9, 1), moment(16, 12))])
        self.assertEqual(available_intervals(date(2026, 11, 16), preference, [], moment(16, 12)), [])

    def test_daily_capacity_is_capped_and_busy_minutes_are_not_double_counted(self):
        self.event(moment(16, 9), moment(16, 11))
        self.event(moment(16, 10), moment(16, 12))
        preference = StudyPreference(owner=self.owner, study_start=time(8), study_end=time(14), max_daily_minutes=120)
        monday = build_week(self.owner, date(2026, 11, 16), preference, now=moment(15))[0]
        self.assertEqual([(item["start_label"], item["end_label"]) for item in monday["free"]],
                         [("08:00", "09:00"), ("12:00", "14:00")])
        self.assertEqual(sum(item["minutes"] for item in monday["free"]), 180)
        self.assertEqual(monday["capacity_minutes"], 120)


class PlannerFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(username="planner_a")
        cls.other = User.objects.create_user(username="planner_b")
        cls.busy = BusyEvent.objects.create(
            owner=cls.owner, title="Own weekly class", starts_at=moment(2, 9), ends_at=moment(2, 11),
            repeat_weekly=True, repeat_until=date(2026, 11, 23),
        )
        cls.private = BusyEvent.objects.create(
            owner=cls.other, title="Private calendar B", starts_at=moment(17, 8), ends_at=moment(17, 12)
        )
        cls.task = Task.objects.create(
            owner=cls.owner, title="Own deadline", deadline=moment(18, 21),
            estimated_minutes=60, remaining_minutes=60,
        )
        cls.other_task = Task.objects.create(
            owner=cls.other, title="Private deadline B", deadline=moment(18, 22),
            estimated_minutes=60, remaining_minutes=60,
        )

    def setUp(self):
        self.client.force_login(self.owner)

    def busy_data(self, **extra):
        data = {"title": "Work shift", "starts_at": "2026-11-17T18:00", "ends_at": "2026-11-17T22:00"}
        data.update(extra)
        return data

    def preference_data(self, **extra):
        data = {
            "study_days": ["0", "1", "2", "3", "4", "5", "6"],
            "study_start": "08:00", "study_end": "22:00", "max_daily_minutes": 240,
            "session_minutes": 50, "break_minutes": 10,
        }
        data.update(extra)
        return data

    def test_all_planner_pages_require_login(self):
        client = Client()
        for name in ("week", "preferences", "busy_list", "busy_create", "busy_update", "busy_delete"):
            args = [self.busy.pk] if name in ("busy_update", "busy_delete") else []
            response = client.get(reverse(f"planner:{name}", args=args))
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_reading_calendar_and_default_preferences_does_not_create_database_rows(self):
        for name in ("week", "preferences"):
            response = self.client.get(reverse(f"planner:{name}"))
            self.assertEqual(response.status_code, 200)
        self.assertFalse(StudyPreference.objects.filter(owner=self.owner).exists())

    def test_week_normalizes_to_monday_and_hides_other_users_data(self):
        response = self.client.get(reverse("planner:week"), {"week": "2026-11-18"})
        self.assertEqual(response.context["week_start"], date(2026, 11, 16))
        self.assertEqual(response.context["week_end"], date(2026, 11, 22))
        self.assertEqual(response.context["previous_week"], "2026-11-09")
        self.assertEqual(response.context["next_week"], "2026-11-23")
        self.assertContains(response, self.busy.title)
        self.assertContains(response, self.task.title)
        self.assertNotContains(response, self.private.title)
        self.assertNotContains(response, self.other_task.title)
        self.assertNotContains(self.client.get(reverse("planner:busy_list")), self.private.title)

    def test_deadlines_at_week_boundaries_and_completed_deadlines(self):
        first = Task.objects.create(owner=self.owner, title="Monday midnight", deadline=moment(16),
                                    estimated_minutes=30, remaining_minutes=0, status=Task.Status.DONE)
        Task.objects.create(owner=self.owner, title="Next Monday", deadline=moment(23),
                            estimated_minutes=30, remaining_minutes=30)
        days = build_week(self.owner, date(2026, 11, 16), StudyPreference(owner=self.owner), now=moment(15))
        deadlines = [item["task"] for day in days for item in day["items"] if item["kind"] == "deadline"]
        self.assertSetEqual(set(deadlines), {first, self.task})

    def test_invalid_and_out_of_range_week_parameters_show_errors(self):
        for value in ("bad-date", "2026-02-30", "0001-01-01", "9999-12-31"):
            with self.subTest(value=value):
                response = self.client.get(reverse("planner:week"), {"week": value})
                self.assertEqual(response.status_code, 200)
                self.assertIn("week", response.context["week_form"].errors)
                self.assertNotIn("days", response.context)

    def test_busy_create_update_and_disable_recurrence_ignore_forged_owner(self):
        response = self.client.post(reverse("planner:busy_create"), self.busy_data(
            owner=self.other.pk, repeat_weekly="on", repeat_until="2026-11-30"
        ))
        self.assertRedirects(response, reverse("planner:busy_list"))
        event = BusyEvent.objects.get(title="Work shift")
        self.assertEqual(event.owner, self.owner)
        self.assertTrue(event.repeat_weekly)
        self.assertEqual(event.starts_at, moment(17, 18))
        response = self.client.post(reverse("planner:busy_update", args=[event.pk]), self.busy_data(
            title="Updated shift", ends_at="2026-11-18T02:00", repeat_until="2026-11-30"
        ))
        self.assertRedirects(response, reverse("planner:busy_list"))
        event.refresh_from_db()
        self.assertEqual(event.ends_at, moment(18, 2))
        self.assertFalse(event.repeat_weekly)
        self.assertIsNone(event.repeat_until)

    def test_busy_time_and_recurrence_validation(self):
        cases = [
            ({"title": ""}, "title"),
            ({"ends_at": "2026-11-17T18:00"}, "ends_at"),
            ({"ends_at": "2026-11-17T17:00"}, "ends_at"),
            ({"starts_at": "not-a-date"}, "starts_at"),
            ({"repeat_weekly": "on", "ends_at": "2026-11-24T18:00"}, "ends_at"),
            ({"repeat_weekly": "on", "repeat_until": "2026-11-16"}, "repeat_until"),
        ]
        for changes, field in cases:
            with self.subTest(changes=changes):
                response = self.client.post(reverse("planner:busy_create"), self.busy_data(**changes))
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["form"].errors)
                self.assertEqual(BusyEvent.objects.count(), 2)

    def test_foreign_busy_id_cannot_be_read_edited_or_deleted(self):
        for action in ("busy_update", "busy_delete"):
            path = reverse(f"planner:{action}", args=[self.private.pk])
            for method in (self.client.get, self.client.post):
                self.assertEqual(method(path, {}).status_code, 404)
        self.private.refresh_from_db()
        self.assertEqual(self.private.title, "Private calendar B")

    def test_busy_delete_requires_post_confirmation_and_keeps_tasks(self):
        path = reverse("planner:busy_delete", args=[self.busy.pk])
        self.assertEqual(self.client.get(path).status_code, 200)
        self.assertTrue(BusyEvent.objects.filter(pk=self.busy.pk).exists())
        self.assertRedirects(self.client.post(path), reverse("planner:busy_list"))
        self.assertFalse(BusyEvent.objects.filter(pk=self.busy.pk).exists())
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())

    def test_preferences_are_created_and_updated_only_for_current_user(self):
        private = StudyPreference.objects.create(owner=self.other, max_daily_minutes=180)
        response = self.client.post(reverse("planner:preferences"), self.preference_data(owner=self.other.pk, study_days=["0", "2"]))
        self.assertRedirects(response, reverse("planner:week"))
        preference = StudyPreference.objects.get(owner=self.owner)
        self.assertEqual(preference.study_days, [0, 2])
        self.client.post(reverse("planner:preferences"), self.preference_data(study_start="09:00", max_daily_minutes=180))
        preference.refresh_from_db()
        private.refresh_from_db()
        self.assertEqual(preference.study_start, time(9))
        self.assertEqual(private.max_daily_minutes, 180)
        self.assertEqual(StudyPreference.objects.filter(owner=self.owner).count(), 1)

    def test_no_selected_study_days_is_valid_and_has_no_free_intervals(self):
        response = self.client.post(reverse("planner:preferences"), self.preference_data(study_days=[]))
        self.assertRedirects(response, reverse("planner:week"))
        preference = StudyPreference.objects.get(owner=self.owner)
        self.assertEqual(preference.study_days, [])
        days = build_week(self.owner, date(2026, 11, 16), preference, now=moment(15))
        self.assertTrue(all(not day["free"] and day["capacity_minutes"] == 0 for day in days))

    def test_invalid_preference_windows_lengths_and_days_are_rejected(self):
        cases = [
            ({"study_end": "08:00"}, "study_end"),
            ({"study_end": "07:00"}, "study_end"),
            ({"max_daily_minutes": 0}, "max_daily_minutes"),
            ({"max_daily_minutes": 1441}, "max_daily_minutes"),
            ({"session_minutes": 0}, "session_minutes"),
            ({"session_minutes": 300}, "session_minutes"),
            ({"study_end": "08:30", "session_minutes": 50}, "session_minutes"),
            ({"break_minutes": -1}, "break_minutes"),
            ({"break_minutes": 1441}, "break_minutes"),
            ({"study_days": ["7"]}, "study_days"),
            ({"study_days": ["0", "0"]}, "study_days"),
        ]
        for changes, field in cases:
            with self.subTest(changes=changes):
                response = self.client.post(reverse("planner:preferences"), self.preference_data(**changes))
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["form"].errors)
                self.assertFalse(StudyPreference.objects.filter(owner=self.owner).exists())

    def test_json_study_days_model_validation_rejects_invalid_types(self):
        for days in ([True], [7], [0, 0], [0, []], "0,1"):
            with self.subTest(days=days):
                preference = StudyPreference(owner=self.owner, study_days=days)
                with self.assertRaises(ValidationError) as error:
                    preference.full_clean()
                self.assertIn("study_days", error.exception.message_dict)

    def test_all_planner_mutations_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        for name in ("preferences", "busy_create", "busy_update", "busy_delete"):
            args = [self.busy.pk] if name in ("busy_update", "busy_delete") else []
            self.assertEqual(client.post(reverse(f"planner:{name}", args=args), {}).status_code, 403)
        path = reverse("planner:busy_create")
        client.get(path)
        response = client.post(path, self.busy_data(csrfmiddlewaretoken=client.cookies["csrftoken"].value))
        self.assertRedirects(response, reverse("planner:busy_list"))

    def test_database_rejects_invalid_time_windows_and_daily_limits(self):
        preference = StudyPreference.objects.create(owner=self.owner)
        for changes in ({"study_end": time(7)}, {"max_daily_minutes": 0}, {"session_minutes": 250}):
            with self.assertRaises(IntegrityError), transaction.atomic():
                StudyPreference.objects.filter(pk=preference.pk).update(**changes)
        with self.assertRaises(IntegrityError), transaction.atomic():
            BusyEvent.objects.filter(pk=self.busy.pk).update(ends_at=self.busy.starts_at)
