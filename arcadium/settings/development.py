"""Development settings."""

from .base import *  # noqa: F403

DEBUG = False

ALLOWED_HOSTS: list[str] = [ "localhost", "127.0.0.1", "178.104.137.48", "arcadiumcloud.com", "www.arcadiumcloud.com", "app.arcadiumcloud.com", ]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}
STATIC_ROOT = BASE_DIR / "staticfiles"