"""End-to-end tests for the resumes app."""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.django_db]


def test_editor_page_loads(live_server, browser_page):
    browser_page.goto(f"{live_server.url}/resume/edit/")
    browser_page.wait_for_selector("text=Resume Builder")

    assert browser_page.locator("#preview-pane").is_visible()
    assert browser_page.locator('input[name="full_name"]').is_visible()


def test_editor_autosave_and_preview_update(live_server, browser_page):
    browser_page.goto(f"{live_server.url}/resume/edit/")
    browser_page.fill('input[name="full_name"]', "Grace Hopper")
    browser_page.locator('input[name="full_name"]').blur()
    browser_page.wait_for_timeout(500)

    assert "Grace Hopper" in browser_page.locator("#preview-pane").inner_text()


def test_export_pdf_download(live_server, browser_page):
    browser_page.goto(f"{live_server.url}/resume/edit/")
    with browser_page.expect_download() as download_info:
        browser_page.locator('a[href*="format=pdf"]').first.click()
    download = download_info.value

    assert download.suggested_filename == "resume.pdf"


def test_analyzer_shows_match_results(live_server, browser_page):
    browser_page.goto(f"{live_server.url}/resume/analyze/")
    browser_page.fill('textarea[name="jd_text"]', "Python Django PostgreSQL leadership automation")
    browser_page.get_by_role("button", name="Analyze").click()
    browser_page.wait_for_selector("#analysis-results")

    assert "%" in browser_page.locator("#analysis-results").inner_text()


def test_certification_add_appears_in_preview(live_server, browser_page):
    page = browser_page
    page.goto(f"{live_server.url}/resume/edit/")
    certifications = page.locator("#certifications-section")
    certifications.get_by_title("Add certification").click()
    page.wait_for_selector("[id^='certification-']")

    cert = page.locator("[id^='certification-']").first
    cert.locator('input[name="name"]').fill("AWS Solutions Architect")
    cert.locator('input[name="issuing_body"]').fill("Amazon")
    cert.locator('input[name="name"]').blur()
    page.wait_for_timeout(900)

    preview = page.locator("#preview-pane")
    assert "AWS Solutions Architect" in preview.inner_text()
    assert "Amazon" in preview.inner_text()


def test_certification_delete_removes_from_preview(live_server, browser_page):
    page = browser_page
    page.goto(f"{live_server.url}/resume/edit/")
    page.locator("#certifications-section").get_by_title("Add certification").click()
    page.wait_for_selector("[id^='certification-']")

    cert = page.locator("[id^='certification-']").first
    cert.locator('input[name="name"]').fill("Temporary Cert")
    cert.locator('input[name="name"]').blur()
    page.wait_for_timeout(900)
    assert "Temporary Cert" in page.locator("#preview-pane").inner_text()

    page.once("dialog", lambda dialog: dialog.accept())
    cert.get_by_title("Remove certification").click()
    page.wait_for_timeout(900)
    assert "Temporary Cert" not in page.locator("#preview-pane").inner_text()


def test_start_over_clears_editor_state(live_server, browser_page):
    page = browser_page
    page.goto(f"{live_server.url}/resume/edit/")
    page.fill('input[name="full_name"]', "Temporary Name")
    page.locator('input[name="full_name"]').blur()
    page.wait_for_timeout(600)
    assert "Temporary Name" in page.locator("#preview-pane").inner_text()

    page.get_by_role("button", name="Start over").click()
    page.wait_for_load_state("networkidle")

    assert page.locator('input[name="full_name"]').input_value() == ""
    assert "Temporary Name" not in page.locator("#preview-pane").inner_text()
