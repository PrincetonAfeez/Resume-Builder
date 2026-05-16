"""WSGI config for the resume builder project."""

from __future__ import annotations

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "resume_builder.settings.prod")

application = get_wsgi_application()
