"""Apps for the resumes app."""

from __future__ import annotations

import logging
import os

from django.apps import AppConfig

logger = logging.getLogger("resumes.startup")


class ResumesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "resumes"

    def ready(self) -> None:
        settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "")
        if not settings_module.endswith("prod"):
            return

        from resumes.services.resume_export import weasyprint_runtime_available

        status = "available" if weasyprint_runtime_available() else "fallback_only"
        logger.info("startup_check weasyprint=%s", status)
