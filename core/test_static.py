import os
from pathlib import Path
import tempfile
from unittest.mock import patch

from django.test import SimpleTestCase

from .storage import DevelopmentStaticFilesStorage


class LocalAssetCacheTests(SimpleTestCase):
    def test_url_changes_after_edit_but_is_stable_without_edit(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "app.css"
            source.write_text("old styles", encoding="utf-8")
            storage = DevelopmentStaticFilesStorage()
            with patch("core.storage.finders.find", return_value=str(source)):
                original = storage.url("css/app.css")
                self.assertEqual(original, storage.url("css/app.css"))
                previous = source.stat().st_mtime_ns
                source.write_text("new calendar layout", encoding="utf-8")
                os.utime(source, ns=(previous + 1_000_000_000, previous + 1_000_000_000))
                self.assertNotEqual(original, storage.url("css/app.css"))
                self.assertIn("/css/app.css?v=", storage.url("css/app.css"))

    def test_missing_asset_keeps_normal_static_url(self):
        with patch("core.storage.finders.find", return_value=None):
            self.assertTrue(DevelopmentStaticFilesStorage().url("missing.css").endswith("/missing.css"))
