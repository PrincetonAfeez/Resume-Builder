"""Fixtures for the resumes app."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from resumes.models import Achievement, Certification, Education, Experience, Profile, Skill

BASE_DIR = Path(__file__).resolve().parents[1]
README_SCREENSHOTS = BASE_DIR / "docs" / "screenshots"


@pytest.fixture
def profile(db) -> Profile:
    profile = Profile.objects.create(
        session_key="test-session",
        full_name="Ada Lovelace",
        email="ada@example.com",
        phone="555-0100",
        location="London, UK",
        linkedin_url="https://linkedin.com/in/ada",
        portfolio_url="https://ada.example.com",
        professional_summary=(
            "Analytical software leader with deep experience building reliable systems "
            "and translating complex ideas into practical tools."
        ),
    )
    experience = Experience.objects.create(
        profile=profile,
        company="Analytical Engines",
        title="Principal Engineer",
        location="Remote",
        start_date="2022-01-01",
        current_role=True,
        order=1,
    )
    Achievement.objects.create(
        experience=experience,
        text="Built 3 automated reporting workflows that reduced manual review time by 40%.",
        order=1,
    )
    Achievement.objects.create(
        experience=experience,
        text="Implemented reliability dashboards used by 12 cross-functional teams.",
        order=2,
    )
    Education.objects.create(
        profile=profile,
        institution="University of London",
        degree="BS",
        field="Mathematics",
        order=1,
    )
    Skill.objects.create(profile=profile, name="Python", category="technical", proficiency=5, order=1)
    Skill.objects.create(profile=profile, name="Django", category="technical", proficiency=5, order=2)
    Skill.objects.create(profile=profile, name="Communication", category="soft", proficiency=4, order=3)
    Certification.objects.create(
        profile=profile,
        name="AWS Solutions Architect",
        issuing_body="Amazon",
        order=1,
    )
    return profile


@pytest.fixture
def bound_profile(client, profile) -> Profile:
    session = client.session
    session.save()
    profile.session_key = session.session_key
    profile.save(update_fields=["session_key"])
    return profile


@pytest.fixture
def locmem_cache(settings):
    settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    return settings


@pytest.fixture
def browser_page() -> Iterator:
    pytest.importorskip("playwright")
    os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        yield page
        browser.close()
