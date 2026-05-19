"""Smoke tests for Django admin registration."""

from __future__ import annotations

import pytest
from django.contrib import admin

from resumes.models import Experience, Profile


@pytest.mark.django_db
def test_profile_and_experience_registered_in_admin():
    assert admin.site.is_registered(Profile)
    assert admin.site.is_registered(Experience)
