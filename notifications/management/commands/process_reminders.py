import time

from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError, close_old_connections

from notifications.services import run_cycle


class Command(BaseCommand):
    help = "Tạo và xử lý nhắc deadline/buổi học. Mặc định chạy một lượt; --watch chạy liên tục."

    def add_arguments(self, parser):
        parser.add_argument("--watch", action="store_true", help="Chạy worker nền liên tục.")
        parser.add_argument("--interval", type=int, default=60, help="Số giây giữa hai lượt (1–3600), mặc định 60.")

    def handle(self, *args, **options):
        if not 1 <= options["interval"] <= 3600:
            raise CommandError("Interval phải từ 1 đến 3600 giây.")
        try:
            while True:
                close_old_connections()
                try:
                    result = run_cycle()
                    self.stdout.write(f"Đã tạo {result['created']} nhắc; xử lý thành công {result['delivered']} nhắc.")
                except OperationalError as error:
                    if "locked" not in str(error).lower():
                        raise
                    if not options["watch"]:
                        raise CommandError("Database đang bận. Hãy chạy lại lượt xử lý nhắc.") from error
                    self.stderr.write("Database đang bận; worker sẽ thử lại ở lượt tiếp theo.")
                if not options["watch"]:
                    break
                time.sleep(options["interval"])
        except KeyboardInterrupt:
            self.stdout.write("Đã dừng worker nhắc việc.")
