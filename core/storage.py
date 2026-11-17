from pathlib import Path

from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import StaticFilesStorage


class DevelopmentStaticFilesStorage(StaticFilesStorage):
    """Change local asset URLs when source files change, avoiding stale browser CSS."""

    def url(self, name):
        url = super().url(name)
        source = finders.find(name)
        if source:
            return f"{url}?v={Path(source).stat().st_mtime_ns}"
        return url
