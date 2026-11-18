"""Run the web and both workers together for a temporary, single-instance demo."""
import os
import signal
import subprocess
import sys
from threading import Event


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.render")
    stopped = Event()
    for name in (signal.SIGTERM, signal.SIGINT):
        signal.signal(name, lambda *_: stopped.set())

    processes = []
    try:
        subprocess.run([sys.executable, "manage.py", "check", "--deploy", "--fail-level", "WARNING"], check=True)
        subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"], check=True)
        if os.getenv("DEMO_ACCOUNT_PASSWORD"):
            subprocess.run([sys.executable, "manage.py", "bootstrap_demo"], check=True)
        for name, command in (
            ("web", ["-m", "deploy.serve"]),
            ("reminders", ["manage.py", "process_reminders", "--watch"]),
            ("calendar", ["manage.py", "process_calendar_sync", "--watch"]),
        ):
            if stopped.is_set():
                return 0
            processes.append((name, subprocess.Popen([sys.executable, *command])))
        while not stopped.wait(1):
            for name, process in processes:
                if process.poll() is not None:
                    print(f"{name} exited; stopping the demo so the host can restart it.", flush=True)
                    return process.returncode or 1
        return 0
    finally:
        for _, process in processes:
            if process.poll() is None:
                process.terminate()
        for _, process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    sys.exit(main())
