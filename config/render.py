"""Render demo: retain production checks and use the platform's hostname/secret."""
import hashlib
import os

from django.core.exceptions import ImproperlyConfigured


hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if hostname:
    os.environ.setdefault("DJANGO_ALLOWED_HOSTS", hostname)
    os.environ.setdefault("SITE_URL", "https://" + hostname)

if not os.getenv("DJANGO_SECRET_KEY"):
    render_secret = os.getenv("RENDER_SECRET_KEY", "")
    if len(render_secret) < 43:
        raise ImproperlyConfigured("Render requires a generated RENDER_SECRET_KEY.")
    # Render generates 256-bit base64 secrets (44 characters); Django expects 50+.
    os.environ["DJANGO_SECRET_KEY"] = hashlib.sha256(render_secret.encode()).hexdigest()

from .production import *


# Let the internal HTTP probe reach the database check instead of redirecting.
SECURE_REDIRECT_EXEMPT = [r"^health/$"]
