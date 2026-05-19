"""Shared test paths (importable without loading conftest)."""

from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
README_SCREENSHOTS = BASE_DIR / "docs" / "screenshots"
