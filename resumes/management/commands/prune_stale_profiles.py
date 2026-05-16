"""Prune stale profiles."""

from __future__ import annotations

import logging

from django.core.management.base import BaseCommand

from resumes.services.profile import prune_stale_profiles

logger = logging.getLogger("resumes.production")


class Command(BaseCommand):
    help = "Delete resume profiles whose backing sessions have expired."

    def handle(self, *args: object, **options: object) -> None:
        deleted = prune_stale_profiles()
        message = f"prune_stale_profiles deleted={deleted}"
        logger.info(message)
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} stale profile(s)."))
