"""Tests for demo profile seeding."""

from __future__ import annotations

import pytest

from resumes.demo import seed_demo_profile
from resumes.models import Achievement, Profile


@pytest.mark.django_db
def test_seed_demo_profile_creates_full_resume():
    profile = seed_demo_profile("demo-session-key")

    assert profile.full_name == "Ada Lovelace"
    assert profile.experiences.count() == 1
    assert Achievement.objects.filter(experience__profile=profile).count() == 2
    assert profile.education.count() == 1
    assert profile.skills.count() == 3


@pytest.mark.django_db
def test_seed_demo_profile_is_idempotent():
    first = seed_demo_profile("demo-session-2")
    second = seed_demo_profile("demo-session-2")

    assert first.pk == second.pk
    assert Profile.objects.filter(session_key="demo-session-2").count() == 1
