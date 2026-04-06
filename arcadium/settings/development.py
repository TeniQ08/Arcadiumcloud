"""Development settings."""

from .base import *  # noqa: F403

DEBUG = True

ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}
STATIC_ROOT = BASE_DIR / "staticfiles"