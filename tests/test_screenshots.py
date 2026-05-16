"""Tests for the screenshots for the resumes app."""

from __future__ import annotations

from tests.conftest import README_SCREENSHOTS

SCREENSHOT_NAMES = ("editor.png", "classic-theme.png", "modern-theme.png", "analyzer.png")
MIN_BYTES = 8_000


def test_readme_screenshot_assets_exist_and_are_non_trivial():
    for name in SCREENSHOT_NAMES:
        path = README_SCREENSHOTS / name
        assert path.is_file(), f"Missing README screenshot: {path}"
        assert path.stat().st_size >= MIN_BYTES, f"Screenshot too small: {path}"

