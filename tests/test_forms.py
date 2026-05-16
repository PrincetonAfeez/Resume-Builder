"""Tests for the forms for the resumes app."""

from __future__ import annotations

import pytest

from resumes.forms import CertificationForm, EducationForm, ExperienceForm
from resumes.models import Certification, Education, Experience, Profile


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
