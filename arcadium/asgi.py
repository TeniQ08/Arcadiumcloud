"""ASGI config for Arcadium."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "arcadium.settings.production")

application = get_asgi_application()
