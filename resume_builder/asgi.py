"""ASGI config for the resume builder project."""

from __future__ import annotations

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "resume_builder.settings.dev")

application = get_asgi_application()
