from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.test import RequestFactory, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from .context_processors import header_notifications
from .models import Reminder


class NotificationHeaderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user("header-owner")
        cls.other = get_user_model().objects.create_user("header-other")

    def reminder(self, **kwargs):
        return Reminder.objects.create(**{
            "owner": self.owner, "kind": Reminder.Kind.DEADLINE, "channel": Reminder.Channel.IN_APP,
            "dedup_key": str(Reminder.objects.count()), "target_at": timezone.now(),
            "remind_at": timezone.now(), "title": "Own notice", "message": "A study reminder",
            "status": Reminder.Status.SENT, "delivered_at": timezone.now(), **kwargs,
        })

    def test_anonymous_header_does_not_read_notifications(self):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        with self.assertNumQueries(0):
            self.assertEqual(header_notifications(request), {})
        response = self.client.get(reverse("core:home"))
        self.assertNotContains(response, 'name="header-menu"')
        self.assertNotContains(response, reverse("accounts:logout"))

    def test_header_limits_preview_but_counts_all_owned_unread_sent_web_notices(self):
        self.reminder(read_at=timezone.now(), title="Old read notice")
        sent = [self.reminder(title=f"Visible own notice {number}") for number in range(7)]
        for attrs in ({"owner": self.other, "title": "Private other account"},
                      {"status": Reminder.Status.PENDING, "title": "Pending private notice"},
                      {"channel": Reminder.Channel.EMAIL, "title": "Email private notice"}):
            self.reminder(**attrs)
        self.client.force_login(self.owner)
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.context["header_unread_count"], 7)
        self.assertEqual(list(response.context["header_reminders"]), list(reversed(sent[-5:])))
        for title in ("Private other account", "Pending private notice", "Email private notice", "Old read notice"):
            self.assertNotContains(response, title)
        self.assertContains(response, f"#reminder-{sent[-1].pk}")
        self.assertContains(self.client.get(reverse("notifications:inbox")), f'id="reminder-{sent[-1].pk}"')

    def test_rendering_header_is_read_only_and_badge_updates_after_explicit_read(self):
        notice = self.reminder()
        self.client.force_login(self.owner)
        with patch("requests.sessions.Session.request") as provider, CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.context["header_unread_count"], 1)
        provider.assert_not_called()
        self.assertTrue(all(query["sql"].lstrip().upper().startswith("SELECT") for query in queries))
        notice.refresh_from_db()
        self.assertIsNone(notice.read_at)
        self.client.post(reverse("notifications:read", args=[notice.pk]))
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.context["header_unread_count"], 0)
        self.assertIn(notice, response.context["header_reminders"])
