"""Tests for the forms for the resumes app."""

from __future__ import annotations

import pytest

from resumes.forms import (
    AchievementForm,
    CertificationForm,
    EducationForm,
    ExperienceForm,
    PersonalInfoForm,
    SkillForm,
    SummaryForm,
    ThemeForm,
)
from resumes.models import Achievement, Certification, Education, Experience, Profile, Skill


@pytest.mark.django_db
def test_experience_form_rejects_end_before_start():
    experience = Experience.objects.create(profile=Profile.objects.create(session_key="form-test"))
    form = ExperienceForm(
        data={
            "company": "Acme",
            "title": "Engineer",
            "location": "",
            "start_date": "2024-06-01",
            "end_date": "2024-01-01",
            "current_role": False,
        },
        instance=experience,
    )

    assert not form.is_valid()
    assert "end_date" in form.errors


@pytest.mark.django_db
def test_experience_form_rejects_end_date_on_current_role():
    experience = Experience.objects.create(profile=Profile.objects.create(session_key="form-test-2"))
    form = ExperienceForm(
        data={
            "company": "Acme",
            "title": "Engineer",
            "location": "",
            "start_date": "2024-01-01",
            "end_date": "2024-06-01",
            "current_role": True,
        },
        instance=experience,
    )

    assert not form.is_valid()
    assert "end_date" in form.errors


@pytest.mark.django_db
def test_education_form_rejects_invalid_range():
    education = Education.objects.create(profile=Profile.objects.create(session_key="edu-form"))
    form = EducationForm(
        data={
            "institution": "University",
            "degree": "BS",
            "field": "CS",
            "start_date": "2022-01-01",
            "end_date": "2020-01-01",
            "gpa": "",
            "notes": "",
        },
        instance=education,
    )

    assert not form.is_valid()
    assert "end_date" in form.errors


@pytest.mark.django_db
def test_certification_form_rejects_expiry_before_earned():
    certification = Certification.objects.create(profile=Profile.objects.create(session_key="cert-form"))
    form = CertificationForm(
        data={
            "name": "AWS",
            "issuing_body": "Amazon",
            "date_earned": "2024-06-01",
            "expiry": "2020-01-01",
            "credential_id": "",
        },
        instance=certification,
    )

    assert not form.is_valid()
    assert "expiry" in form.errors


@pytest.mark.django_db
def test_personal_info_form_valid(profile):
    form = PersonalInfoForm(
        data={
            "full_name": "Ada Lovelace",
            "email": "ada@example.com",
            "phone": "555",
            "location": "London",
            "linkedin_url": "",
            "portfolio_url": "",
        },
        instance=profile,
    )

    assert form.is_valid()


@pytest.mark.django_db
def test_summary_and_theme_forms_valid(profile):
    assert SummaryForm(data={"professional_summary": "Summary"}, instance=profile).is_valid()
    assert ThemeForm(
        data={"chosen_theme": "modern", "accent_color": "blue", "font_pairing": "sans"},
        instance=profile,
    ).is_valid()


@pytest.mark.django_db
def test_skill_form_accepts_proficiency(profile):
    skill = Skill.objects.create(profile=profile, name="", order=99)
    form = SkillForm(
        data={"name": "Rust", "category": "technical", "proficiency": "4"},
        instance=skill,
    )

    assert form.is_valid()


@pytest.mark.django_db
def test_achievement_form_valid(profile):
    experience = profile.experiences.first()
    assert experience is not None
    achievement = Achievement.objects.create(experience=experience, text="", order=99)
    form = AchievementForm(data={"text": "Shipped 3 releases."}, instance=achievement)

    assert form.is_valid()


@pytest.mark.django_db
def test_achievement_form_rejects_text_over_180_characters(profile):
    experience = profile.experiences.first()
    assert experience is not None
    achievement = Achievement.objects.create(experience=experience, text="ok", order=99)
    form = AchievementForm(data={"text": "x" * 181}, instance=achievement)

    assert not form.is_valid()
    assert "text" in form.errors
    assert "180" in form.errors["text"][0]


@pytest.mark.django_db
def test_experience_form_valid_current_role(profile):
    experience = Experience.objects.create(profile=profile, order=99)
    form = ExperienceForm(
        data={
            "company": "Acme",
            "title": "Engineer",
            "location": "",
            "start_date": "2024-01-01",
            "end_date": "",
            "current_role": True,
        },
        instance=experience,
    )

    assert form.is_valid()
