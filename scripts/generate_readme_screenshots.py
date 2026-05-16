"""Generate docs/screenshots for the README using Playwright."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SCREENSHOTS_DIR = BASE_DIR / "docs" / "screenshots"
SERVER = "http://127.0.0.1:18765"
SCREENSHOT_NAMES = ("editor.png", "classic-theme.png", "modern-theme.png", "analyzer.png")


def _django_setup() -> None:
    sys.path.insert(0, str(BASE_DIR))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "resume_builder.settings.dev")
    import django

    django.setup()


def generate_screenshots() -> list[Path]:
    _django_setup()

    from django.contrib.sessions.backends.db import SessionStore

    from resumes.demo import seed_demo_profile

    store = SessionStore()
    store.create()
    store.save()
    seed_demo_profile(store.session_key)

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    server = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", "18765", "--noreload"],
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2.5)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        server.terminate()
        raise SystemExit(
            "Playwright is required. Install with: python -m pip install playwright && playwright install chromium"
        ) from exc

    written: list[Path] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            context.add_cookies(
                [
                    {
                        "name": "sessionid",
                        "value": store.session_key,
                        "domain": "127.0.0.1",
                        "path": "/",
                    }
                ]
            )
            page = context.new_page()

            page.goto(f"{SERVER}/resume/edit/", wait_until="networkidle")
            written.append(SCREENSHOTS_DIR / "editor.png")
            page.screenshot(path=written[-1], full_page=True)

            written.append(SCREENSHOTS_DIR / "classic-theme.png")
            page.locator("#preview-pane .paper").screenshot(path=written[-1])

            page.locator('input[name="chosen_theme"][value="modern"]').check()
            page.wait_for_timeout(1200)
            written.append(SCREENSHOTS_DIR / "modern-theme.png")
            page.locator("#preview-pane .paper").screenshot(path=written[-1])

            page.goto(f"{SERVER}/resume/analyze/", wait_until="networkidle")
            page.fill(
                'textarea[name="jd_text"]',
                "Python Django PostgreSQL automation reporting reliability cross-functional leadership.",
            )
            page.get_by_role("button", name="Analyze").click()
            page.wait_for_selector("#analysis-results .keyword, #analysis-results .empty-state")
            written.append(SCREENSHOTS_DIR / "analyzer.png")
            page.locator("section.editor-panel").screenshot(path=written[-1])

            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=10)

    return written


def main() -> None:
    paths = generate_screenshots()
    print(f"Wrote {len(paths)} screenshots to {SCREENSHOTS_DIR}")


if __name__ == "__main__":
    main()
