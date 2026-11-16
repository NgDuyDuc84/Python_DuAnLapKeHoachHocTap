from datetime import date, datetime
from html.parser import HTMLParser
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from focus.forms import LogRangeForm
from focus.models import StudyLog
from studies.models import Task


class Inputs(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.fields = {}
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input" and "name" in attrs:
            self.fields[attrs["name"]] = attrs


class DateTimeInputTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user("date-owner")
        cls.other = get_user_model().objects.create_user("date-other")

    def setUp(self):
        self.client.force_login(self.owner)

    def task_data(self, **overrides):
        return {
            "title": "Deadline ISO", "deadline": "2026-12-01T22:45",
            "priority": "2", "estimated_minutes": "45", "can_split": "on",
            "status": "todo", **overrides,
        }

    def test_task_deadline_still_accepts_iso_and_uses_vietnam_timezone(self):
        response = self.client.post(reverse("studies:task_create"), self.task_data(owner=self.other.pk))
        self.assertRedirects(response, reverse("studies:task_list"))
        task = Task.objects.get(title="Deadline ISO")
        self.assertEqual(task.owner, self.owner)
        self.assertEqual(timezone.localtime(task.deadline).isoformat(), "2026-12-01T22:45:00+07:00")
        response = self.client.get(reverse("studies:task_update", args=[task.pk]))
        field = Inputs(response.content.decode()).fields["deadline"]
        self.assertEqual((field["type"], field["value"]), ("datetime-local", "2026-12-01T22:45"))

    @patch("focus.forms.timezone.localdate", return_value=date(2026, 11, 16))
    def test_statistics_iso_range_matches_day_month_chart_labels(self, _today):
        StudyLog.objects.create(owner=self.owner, task_title="Học tháng 11", studied_on=date(2026, 11, 10), minutes=35)
        StudyLog.objects.create(owner=self.owner, task_title="Học tháng 10", studied_on=date(2026, 10, 11), minutes=90)
        StudyLog.objects.create(owner=self.other, task_title="Dữ liệu riêng", studied_on=date(2026, 11, 10), minutes=80)
        data = {"start": "2026-11-10", "end": "2026-11-16"}
        form = LogRangeForm(data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["start"], date(2026, 11, 10))
        response = self.client.get(reverse("focus:statistics"), data)
        self.assertEqual(response.context["totals"]["minutes"], 35)
        self.assertContains(response, '<time datetime="2026-11-10">10/11/2026</time>', html=True)
        fields = Inputs(response.content.decode()).fields
        for name, value in data.items():
            self.assertEqual((fields[name]["type"], fields[name]["value"]), ("date", value))

    def test_shared_task_form_keeps_iso_deadline_and_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        url = reverse("studies:task_create")
        response = client.get(url)
        fields = Inputs(response.content.decode()).fields
        self.assertEqual(fields["deadline"]["type"], "datetime-local")
        self.assertContains(response, "js/datetime_inputs.js")
        self.assertEqual(client.post(url, self.task_data()).status_code, 403)
        response = client.post(url, self.task_data(
            title="Deadline từ form dùng chung", deadline="2026-11-19T08:15",
            owner=self.other.pk, csrfmiddlewaretoken=client.cookies["csrftoken"].value,
        ))
        self.assertRedirects(response, reverse("studies:task_list"))
        task = Task.objects.get(title="Deadline từ form dùng chung")
        self.assertEqual(task.owner, self.owner)
        self.assertEqual(timezone.localtime(task.deadline), timezone.make_aware(datetime(2026, 11, 19, 8, 15)))

    def test_native_inputs_and_local_assets_cover_all_form_types(self):
        pages = (
            ("focus:statistics", {"start": "date", "end": "date"}),
            ("focus:logs", {"start": "date", "end": "date"}),
            ("focus:log_create", {"studied_on": "date"}),
            ("planner:plan_generate", {"week": "date"}),
            ("planner:preferences", {"study_start": "time", "study_end": "time"}),
            ("planner:busy_create", {"starts_at": "datetime-local", "ends_at": "datetime-local", "repeat_until": "date"}),
            ("studies:task_create", {"deadline": "datetime-local"}),
            ("integrations:google", {}),
        )
        for name, expected in pages:
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                fields = Inputs(response.content.decode()).fields
                for field, kind in expected.items():
                    self.assertEqual(fields[field]["type"], kind)
                for asset in ("vendor/flatpickr/flatpickr.min.css", "vendor/flatpickr/flatpickr.min.js",
                              "vendor/flatpickr/vn.js", "js/datetime_inputs.js"):
                    self.assertContains(response, asset, count=1)
