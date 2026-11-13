import time

from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError, close_old_connections

from integrations.services import run_cycle


class Command(BaseCommand):
    help = "Sync user-confirmed study weeks to Google Calendar."

    def add_arguments(self, parser):
        parser.add_argument("--watch", action="store_true")
        parser.add_argument("--interval", type=int, default=60)

    def handle(self, *args, **options):
        if not 1 <= options["interval"] <= 3600:
            raise CommandError("Interval must be between 1 and 3600 seconds.")
        try:
            while True:
                close_old_connections()
                try:
                    count = run_cycle()
                    self.stdout.write(f"Google Calendar: processed {count} sync job(s).")
                except OperationalError as exc:
                    if "locked" not in str(exc).lower():
                        raise
                    if not options["watch"]:
                        raise CommandError("Database is busy; try again.") from exc
                    self.stderr.write("Database is busy; retrying in the next cycle.")
                if not options["watch"]:
                    break
                time.sleep(options["interval"])
        except KeyboardInterrupt:
            self.stdout.write("Google Calendar worker stopped.")
