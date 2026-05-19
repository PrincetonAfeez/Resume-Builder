from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]


def test_prod_settings_reject_default_secret_key():
    env = os.environ.copy()
    env.update(
        {
            "DJANGO_SETTINGS_MODULE": "resume_builder.settings.prod",
            "SECRET_KEY": "dev-only-change-me",
            "DATABASE_URL": "postgres://user:pass@localhost:5432/resume",
            "ALLOWED_HOSTS": "example.com",
            "DJANGO_READ_DOT_ENV_FILE": "False",
        }
    )
    result = subprocess.run(
        [sys.executable, "-c", "import resume_builder.settings.prod"],
        cwd=BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "SECRET_KEY must be set in production" in result.stderr + result.stdout


def test_prod_settings_load_with_real_secret_key():
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
        [
            sys.executable,
            "-c",
            "import resume_builder.settings.prod as s; print(s.CACHES['default']['BACKEND'])",
        ],
        cwd=BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "DatabaseCache" in result.stdout
