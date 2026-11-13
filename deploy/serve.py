"""Run behind an HTTPS reverse proxy; keep the application port private."""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.production")

from config.wsgi import application
from waitress import serve


if __name__ == "__main__":
    proxy = os.getenv("TRUSTED_PROXY") or None
    serve(
        application, host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", "8000")), threads=4,
        trusted_proxy=proxy,
        trusted_proxy_headers={"x-forwarded-proto"} if proxy else set(),
        clear_untrusted_proxy_headers=True,
    )
