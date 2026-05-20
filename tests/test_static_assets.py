"""Tests for static assets required by CSP (no inline script/style)."""

from __future__ import annotations

from pathlib import Path

import pytest
from django.conf import settings
from django.test import Client

BASE_DIR = Path(settings.BASE_DIR)


def test_app_js_exists():
    path = BASE_DIR / "resumes" / "static" / "resumes" / "js" / "app.js"
    assert path.is_file()
    content = path.read_text(encoding="utf-8")
    assert "htmx:configRequest" in content
    assert "resume:saved" in content


@pytest.mark.django_db
def test_edit_page_loads_external_app_js(client):
    response = client.get("/resume/edit/")

    assert response.status_code == 200
    assert b"/static/resumes/js/app.js" in response.content
    assert b"htmx:configRequest" not in response.content
    assert b'style="width:' not in response.content
    assert b"<progress" in response.content
    assert b"completeness-progress" in response.content
