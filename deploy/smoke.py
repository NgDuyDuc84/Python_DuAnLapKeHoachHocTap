"""HTTP smoke check for an isolated local test installation, without provider keys."""
import argparse
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
import re
import secrets
import time
from urllib.parse import urljoin, urlsplit

import requests


def local_base(value):
    parts = urlsplit(value)
    if (parts.scheme != "http" or parts.hostname not in ("127.0.0.1", "localhost", "::1")
            or parts.username is not None or parts.password is not None
            or parts.path not in ("", "/") or parts.query or parts.fragment):
        raise argparse.ArgumentTypeError("Use an HTTP loopback origin, e.g. http://127.0.0.1:8000")
    try:
        parts.port
    except ValueError as error:
        raise argparse.ArgumentTypeError("Invalid local port") from error
    return value.rstrip("/") + "/"


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.hidden = {}
        self.links = []
        self.styles = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input" and attrs.get("type") == "hidden" and attrs.get("name"):
            self.hidden[attrs["name"]] = attrs.get("value", "")
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.styles.append(attrs["href"])


class SmokeError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise SmokeError(message)


class LocalWeb:
    def __init__(self, base):
        self.base = local_base(base)
        self.session = requests.Session()
        self.session.trust_env = False

    def url(self, path):
        target = urljoin(self.base, path)
        require(urlsplit(target).netloc == urlsplit(self.base).netloc
                and urlsplit(target).scheme == "http", "Refused a nonlocal link or redirect")
        return target

    def get(self, path, status=200):
        response = self.session.get(self.url(path), timeout=10, allow_redirects=False)
        require(response.status_code == status, f"GET {urlsplit(path).path}: expected {status}, got {response.status_code}")
        return response

    def post(self, form_path, values, *, action=None):
        page = Page(self.get(form_path).text)
        require("csrfmiddlewaretoken" in page.hidden, f"Missing CSRF field at {form_path}")
        response = self.session.post(self.url(action or form_path), data={**page.hidden, **values},
                                     headers={"Referer": self.url(form_path)}, timeout=20, allow_redirects=False)
        require(response.status_code == 302, f"POST {form_path}: expected redirect, got {response.status_code}")
        location = response.headers.get("Location", "")
        require(bool(location), "Missing redirect location")
        self.url(location)
        return location

    def object_id(self, path, pattern):
        matches = [re.fullmatch(pattern, link) for link in Page(self.get(path).text).links]
        ids = {match[1] for match in matches if match}
        require(len(ids) == 1, f"Expected one test object at {path}")
        return ids.pop()


def wait_for_health(web):
    expires = time.monotonic() + 60
    while True:
        try:
            require(web.get("health/").json() == {"status": "ok"}, "Unexpected health response")
            return
        except (requests.RequestException, SmokeError, ValueError):
            if time.monotonic() >= expires:
                raise SmokeError("Local web/database did not become ready within 60 seconds") from None
            time.sleep(1)


def register_and_login(web, username, password):
    web.post("accounts/register/", {"username": username, "email": username + "@example.test",
                                    "password1": password, "password2": password})
    location = web.post("accounts/login/", {"username": username, "password": password})
    require(urlsplit(web.url(location)).path == "/", "Login did not open the dashboard")
    require("Nhịp học của bạn" in web.get(location).text, "Dashboard missing after login")


def journey(web, *, expect_reminders=False):
    marker = "Smoke-" + secrets.token_hex(5)
    password = secrets.token_urlsafe(24) + "!a7"
    today = datetime.now(timezone(timedelta(hours=7))).date()
    monday = today + timedelta(days=7 - today.weekday())
    register_and_login(web, marker.lower() + "a", password)
    print("PASS registration, login and empty dashboard", flush=True)

    web.post("studies/subjects/add/", {"name": marker + " Python", "semester": "Smoke", "color": "#176b58"})
    subject_id = web.object_id("studies/subjects/", r"/studies/subjects/(\d+)/edit/")
    task_values = {"title": marker, "subject": subject_id, "description": "Disposable HTTP test",
                   "deadline": (monday + timedelta(days=4)).isoformat() + "T18:00", "priority": "3",
                   "estimated_minutes": "60", "can_split": "on", "status": "todo"}
    web.post("studies/tasks/add/", task_values)
    task_id = web.object_id("studies/tasks/", r"/studies/tasks/(\d+)/edit/")
    web.post("studies/materials/add/", {"title": marker + " reference", "url": "https://docs.python.org/3/",
                                      "subject": subject_id, "task": task_id, "description": "Test reference"})
    require(marker + " reference" in web.get("studies/materials/").text, "Reference was not saved")
    web.post("planner/busy/add/", {"title": marker + " class", "starts_at": monday.isoformat() + "T09:00",
                                   "ends_at": monday.isoformat() + "T10:00", "repeat_weekly": "on"})
    web.post("planner/preferences/", {"study_days": [str(day) for day in range(7)], "study_start": "08:00",
                                      "study_end": "18:00", "max_daily_minutes": "120",
                                      "session_minutes": "30", "break_minutes": "10"})
    print("PASS subject, task, reference, busy calendar and study preferences", flush=True)

    plan = web.post("planner/plans/new/", {"week": monday.isoformat(), "mode": "add"})
    require(re.fullmatch(r"/planner/plans/\d+/", plan), "Unexpected preview URL")
    preview = web.get(plan)
    require(marker in preview.text and "60 phút trong bản này" in preview.text, "Expected 60 scheduled minutes")
    calendar = web.post(plan, {}, action=plan + "apply/")
    require(marker in web.get(calendar).text, "Applied sessions missing from calendar")
    applied = web.get(plan)
    require("Đã áp dụng" in applied.text, "Plan was not applied")
    session_id = re.search(r"/planner/sessions/(\d+)/edit/", applied.text)
    require(session_id is not None, "Applied session missing")
    web.post(plan, {"locked": "true"}, action=f"planner/sessions/{session_id[1]}/lock/")
    require("Đã khóa" in web.get(plan).text, "Session was not locked")
    print("PASS schedule preview, apply and session lock", flush=True)

    focus = web.post("focus/", {"task": task_id})
    require(re.fullmatch(r"/focus/sessions/\d+/", focus), "Unexpected focus URL")
    web.post(focus, {}, action=focus + "pause/")
    require(web.get(focus + "state/").json()["status"] == "paused", "Focus did not pause")
    web.post(focus, {}, action=focus + "resume/")
    require(web.get(focus + "state/").json()["status"] == "running", "Focus did not resume")
    web.post(focus, {}, action=focus + "cancel/")
    web.post("focus/logs/add/", {"task": task_id, "studied_on": today.isoformat(), "minutes": "25", "notes": marker})
    require("<strong>25</strong>" in web.get("focus/statistics/").text, "Statistics did not total 25 minutes")
    require(marker in web.get("focus/logs/").text, "Study log missing")
    print("PASS focus start/pause/resume/cancel, manual log and statistics", flush=True)

    for path in ("planner/alerts/", "notifications/", "notifications/preferences/",
                 "integrations/google/", "insights/", "accounts/profile/"):
        web.get(path)
    other = LocalWeb(web.base)
    try:
        register_and_login(other, marker.lower() + "b", password)
        other.get(f"studies/tasks/{task_id}/edit/", status=404)
        other.get(plan, status=404)
        other.get(focus, status=404)
        require(marker not in other.get("studies/tasks/").text, "Other account can see private tasks")
    finally:
        other.session.close()
    print("PASS supporting pages and isolation between two accounts", flush=True)

    sidebar = f"planner/?week={monday.isoformat()}&panel=subjects"
    location = web.post(sidebar + "&action=new", {"operation": "save", "name": marker + " sidebar", "color": "#176b58"})
    require("week=" + monday.isoformat() in location and marker + " sidebar" in web.get(location).text,
            "Sidebar did not retain the selected week and new subject")
    task_sidebar = f"planner/?week={monday.isoformat()}&panel=tasks"
    location = web.post(task_sidebar + f"&action=edit&id={task_id}", {
        **task_values, "operation": "save", "object_id": task_id, "remaining_minutes": "60",
    })
    html = web.get(location).text
    require(all(f"<h4>{label}</h4>" in html for label in ("Sáng", "Chiều", "Tối")), "Missing calendar periods")
    print("PASS inline study sidebar and morning/afternoon/evening calendar", flush=True)

    if expect_reminders:
        due = datetime.now(timezone(timedelta(hours=7))) + timedelta(hours=2)
        web.post("studies/tasks/add/", {**task_values, "title": marker + " reminder", "deadline": due.strftime("%Y-%m-%dT%H:%M")})
        expires = time.monotonic() + 90
        while marker + " reminder" not in web.get("notifications/").text:
            require(time.monotonic() < expires, "Reminder worker did not deliver within 90 seconds")
            time.sleep(2)
        print("PASS in-app reminder delivered by background worker", flush=True)
    print("PASS complete HTTP journey (two disposable accounts retained in the test database)", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", type=local_base, default="http://127.0.0.1:8000/")
    parser.add_argument("--allow-test-data", action="store_true", help="Create two disposable accounts and study records")
    parser.add_argument("--expect-reminders", action="store_true", help="Also wait for a running reminder worker")
    args = parser.parse_args()
    if args.expect_reminders and not args.allow_test_data:
        parser.error("--expect-reminders requires --allow-test-data")
    web = LocalWeb(args.base_url)
    try:
        wait_for_health(web)
        styles = Page(web.get("/").text).styles
        require(bool(styles), "No stylesheet linked from landing page")
        require("text/css" in web.get(styles[0]).headers.get("Content-Type", ""), "Static CSS not served")
        print("PASS health, landing page and static CSS", flush=True)
        if args.allow_test_data:
            journey(web, expect_reminders=args.expect_reminders)
    except (SmokeError, requests.RequestException) as error:
        # Do not print response bodies, form data, credentials or network exception URLs.
        message = str(error) if isinstance(error, SmokeError) else "Local HTTP request failed"
        parser.exit(1, "FAIL " + message + "\n")
    finally:
        web.session.close()


if __name__ == "__main__":
    main()
