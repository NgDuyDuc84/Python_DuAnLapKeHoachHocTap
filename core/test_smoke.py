import argparse

from django.test import SimpleTestCase

from deploy.smoke import LocalWeb, Page, SmokeError, local_base


class HttpSmokeSafetyTests(SimpleTestCase):
    def test_only_loopback_http_origins_are_accepted(self):
        for value in ("https://example.com", "http://192.168.1.1", "http://localhost.evil.test",
                      "http://user:pass@localhost", "http://localhost/path", "http://localhost/?key=secret",
                      "http://localhost/#fragment", "http://localhost:bad"):
            with self.subTest(value=value), self.assertRaises((argparse.ArgumentTypeError, ValueError)):
                local_base(value)
        for value in ("http://127.0.0.1:8000", "http://localhost:8001/", "http://[::1]:8000"):
            self.assertTrue(local_base(value).endswith("/"))

    def test_external_links_and_redirects_cannot_receive_test_credentials(self):
        web = LocalWeb("http://127.0.0.1:8000")
        try:
            for path in ("https://example.test", "//example.test", "http://127.0.0.1:8001/", "http://user@127.0.0.1:8000"):
                with self.subTest(path=path), self.assertRaises(SmokeError):
                    web.url(path)
            self.assertEqual(web.url("/planner/"), "http://127.0.0.1:8000/planner/")
        finally:
            web.session.close()

    def test_parser_reads_csrf_and_deduplication_keys_without_visible_field_values(self):
        page = Page('<input type="hidden" name="csrfmiddlewaretoken" value="csrf&amp;token">'
                    '<input type="hidden" name="entry_key" value="uuid"><input name="password" value="secret">'
                    '<a href="/planner/">Calendar</a><link rel="stylesheet" href="/static/app.css">')
        self.assertEqual(page.hidden, {"csrfmiddlewaretoken": "csrf&token", "entry_key": "uuid"})
        self.assertEqual(page.links, ["/planner/"])
        self.assertEqual(page.styles, ["/static/app.css"])
