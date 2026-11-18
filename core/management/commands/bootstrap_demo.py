import os

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


DEMO_ACCOUNTS = (
    ("nguyen_van_a", "Nguyễn Văn A"),
    ("tran_thi_b", "Trần Thị B"),
    ("le_van_c", "Lê Văn C"),
)


class Command(BaseCommand):
    help = "Provision the three presentation accounts using DEMO_ACCOUNT_PASSWORD, without resetting existing data."

    @transaction.atomic
    def handle(self, *args, **options):
        password = os.getenv("DEMO_ACCOUNT_PASSWORD")
        if not password:
            raise CommandError("Set DEMO_ACCOUNT_PASSWORD in the hosting environment first.")
        User = get_user_model()
        for username, name in DEMO_ACCOUNTS:
            user = User.objects.select_for_update().filter(username=username).first()
            if user:
                if user.is_staff or user.is_superuser or not user.is_active or not user.check_password(password):
                    raise CommandError(f"Account {username} already exists with different credentials or permissions; no changes made.")
            else:
                user = User.objects.create_user(username=username, first_name=name, password=password)
            call_command("seed_demo", username=username, stdout=self.stdout)
        self.stdout.write("Presentation accounts ready. Existing passwords and demo progress were preserved.")
