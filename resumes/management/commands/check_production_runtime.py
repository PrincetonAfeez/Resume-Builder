"""Check production runtime."""

from __future__ import annotations

import logging

from django.core.management.base import BaseCommand

from resumes.services.resume_export import weasyprint_runtime_available

logger = logging.getLogger("resumes.production")


class Command(BaseCommand):
    help = "Log production runtime checks (WeasyPrint) during deploy."

    def handle(self, *args: object, **options: object) -> None:
        if weasyprint_runtime_available():
            message = "production_runtime weasyprint=available"
            logger.info(message)
            self.stdout.write(self.style.SUCCESS(message))
        else:
            message = "production_runtime weasyprint=fallback_only"
            logger.warning(message)
            self.stdout.write(self.style.WARNING(message))
