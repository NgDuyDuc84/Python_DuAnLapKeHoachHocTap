from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.test import TestCase

from studies.models import Task


class BootstrapDemoTests(TestCase):
    @patch.dict("os.environ", {"DEMO_ACCOUNT_PASSWORD": "Synthetic-demo-password!"})
    def test_bootstrap_creates_three_isolated_accounts_and_preserves_edits_on_restart(self):
        output = StringIO()
        call_command("bootstrap_demo", stdout=output)
        User = get_user_model()
        self.assertEqual(User.objects.count(), 3)
        for user in User.objects.all():
            self.assertTrue(user.check_password("Synthetic-demo-password!"))
            self.assertFalse(user.is_staff or user.is_superuser)
            self.assertEqual(Task.objects.filter(owner=user).count(), 12)
        task = Task.objects.first()
        task.title = "Edited during the presentation"
        task.save()
        call_command("bootstrap_demo", stdout=output)
        task.refresh_from_db()
        self.assertEqual(task.title, "Edited during the presentation")
        self.assertEqual(Task.objects.count(), 36)

    @patch.dict("os.environ", {"DEMO_ACCOUNT_PASSWORD": "Synthetic-demo-password!"})
    def test_account_collision_rolls_back_without_resetting_existing_credentials(self):
        existing = get_user_model().objects.create_user("tran_thi_b", password="Different-password!")
        password_hash = existing.password
        with self.assertRaises(CommandError):
            call_command("bootstrap_demo", stdout=StringIO())
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertFalse(Task.objects.exists())
        existing.refresh_from_db()
        self.assertEqual(existing.password, password_hash)
