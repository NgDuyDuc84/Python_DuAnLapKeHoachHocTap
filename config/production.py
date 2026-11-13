from urllib.parse import urlsplit

from django.http.request import validate_host

from .assets import *


DEBUG = False
if len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5 or SECRET_KEY.startswith("django-insecure-"):
    raise ImproperlyConfigured("Production requires a private DJANGO_SECRET_KEY of at least 50 characters.")
if not os.getenv("DJANGO_ALLOWED_HOSTS") or "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("Production requires explicit DJANGO_ALLOWED_HOSTS without a wildcard.")
site = urlsplit(SITE_URL)
if site.scheme != "https" or not site.hostname or site.username or site.password or site.path or site.query or site.fragment:
    raise ImproperlyConfigured("Production requires SITE_URL to be an HTTPS origin without a path.")
if not validate_host(site.hostname, ALLOWED_HOSTS):
    raise ImproperlyConfigured("SITE_URL must be included in DJANGO_ALLOWED_HOSTS.")
if DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":
    raise ImproperlyConfigured("Production requires a PostgreSQL DATABASE_URL.")
DATABASES["default"].setdefault("OPTIONS", {}).setdefault("sslmode", "require")

CSRF_TRUSTED_ORIGINS = [SITE_URL]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
