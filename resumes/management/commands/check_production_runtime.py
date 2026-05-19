"""Check production runtime."""

from __future__ import annotations

import logging

from django.core.management.base import BaseCommand, CommandError

from resumes.services.resume_export import weasyprint_runtime_available

logger = logging.getLogger("resumes.production")


class Command(BaseCommand):
    help = "Verify production runtime dependencies (WeasyPrint) during deploy."

    def handle(self, *args: object, **options: object) -> None:
        if weasyprint_runtime_available():
            message = "production_runtime weasyprint=available"
            logger.info(message)
            self.stdout.write(self.style.SUCCESS(message))
            return

        message = "production_runtime weasyprint=unavailable"
        logger.error(message)
        raise CommandError("WeasyPrint native runtime is unavailable; themed PDF export will not work in production.")
