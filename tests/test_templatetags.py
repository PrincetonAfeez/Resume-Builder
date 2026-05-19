"""Tests for resume_forms template tags."""

from __future__ import annotations

import pytest

from resumes.models import Achievement, Certification, Education, Experience, Profile, Skill
from resumes.templatetags.resume_forms import (
    achievement_form,
    bullet_warnings,
    certification_form,
    education_form,
    experience_form,
    skill_form,
    stars,
)


@pytest.mark.django_db
def test_experience_form_filter_returns_bound_instance(profile):
    experience = profile.experiences.first()
    assert experience is not None

    form = experience_form(experience)

    assert form.instance == experience
    assert "company" in form.fields


@pytest.mark.django_db
def test_achievement_form_filter(profile):
    experience = profile.experiences.first()
    assert experience is not None
    achievement = experience.achievements.first()
    assert achievement is not None

    form = achievement_form(achievement)

    assert form.instance == achievement


@pytest.mark.django_db
def test_education_skill_certification_form_filters(profile):
    education = profile.education.first()
    skill = profile.skills.first()
    certification = profile.certifications.first()
    assert education and skill and certification

    assert education_form(education).instance == education
    assert skill_form(skill).instance == skill
    assert certification_form(certification).instance == certification


def test_bullet_warnings_filter_delegates_to_service():
    warnings = bullet_warnings("Responsible for reports")

    assert any(warning.code == "weak_opener" for warning in warnings)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, "-----"),
        (3, "***--"),
        (5, "*****"),
    ],
)
def test_stars_filter(value: int, expected: str):
    assert stars(value) == expected


@pytest.mark.django_db
def test_model_str_representations(profile):
    experience = profile.experiences.first()
    assert experience is not None
    achievement = experience.achievements.first()
    education = profile.education.first()
    skill = profile.skills.first()
    certification = profile.certifications.first()
    assert achievement and education and skill and certification

    assert "Ada" in str(profile)
    assert "Principal" in str(experience)
    assert achievement.text[:10] in str(achievement)
    assert "University" in str(education)
    assert "Python" in str(skill)
    assert "AWS" in str(certification)
