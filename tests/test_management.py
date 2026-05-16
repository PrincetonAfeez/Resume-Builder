"""Tests for the management commands for the resumes app."""

from __future__ import annotations

from io import StringIO

import pytest
from django.core.management import call_command


def test_check_production_runtime_command_logs(capsys):
    out = StringIO()
    call_command("check_production_runtime", stdout=out)
    output = out.getvalue()

    assert "production_runtime weasyprint=" in output


@pytest.mark.django_db
def test_prune_stale_profiles_command_logs(client, caplog):
    import logging

    caplog.set_level(logging.INFO, logger="resumes.production")
    client.get("/resume/edit/")

    from django.contrib.sessions.models import Session

    Session.objects.all().delete()

    out = StringIO()
    call_command("prune_stale_profiles", stdout=out)

    assert "Deleted 1 stale profile" in out.getvalue()
    assert any("prune_stale_profiles deleted=1" in record.message for record in caplog.records)
