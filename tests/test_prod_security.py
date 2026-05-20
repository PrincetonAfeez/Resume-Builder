"""Tests for production security settings."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parents[1]


def _import_prod_setting(name: str) -> str:
    env = os.environ.copy()
    env.update(
        {
            "DJANGO_SETTINGS_MODULE": "resume_builder.settings.prod",
            "SECRET_KEY": "production-secret-key",
            "DATABASE_URL": "postgres://user:pass@localhost:5432/resume",
            "ALLOWED_HOSTS": "example.com",
            "DJANGO_READ_DOT_ENV_FILE": "False",
        }
    )
    result = subprocess.run(
        [sys.executable, "-c", f"import resume_builder.settings.prod as s; print(getattr(s, '{name}', ''))"],
        cwd=BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    return result.stdout.strip()


def test_prod_trust_x_forwarded_for_defaults_true():
    assert _import_prod_setting("TRUST_X_FORWARDED_FOR") == "True"


def test_prod_sets_hsts_and_csp():
    assert _import_prod_setting("SECURE_HSTS_SECONDS") == "31536000"
    assert "default-src 'self'" in _import_prod_setting("CONTENT_SECURITY_POLICY")
    assert "camera=()" in _import_prod_setting("PERMISSIONS_POLICY")


@pytest.mark.django_db
def test_prod_security_headers_on_response(client, settings):
    settings.CONTENT_SECURITY_POLICY = "default-src 'self'"
    settings.PERMISSIONS_POLICY = "camera=()"
    settings.MIDDLEWARE = [
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "resumes.middleware.SecurityHeadersMiddleware",
        "django.middleware.common.CommonMiddleware",
    ]

    response = client.get("/health/")

    assert response["Content-Security-Policy"] == "default-src 'self'"
    assert response["Permissions-Policy"] == "camera=()"
