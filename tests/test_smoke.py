"""Tests for the smoke tests for the resumes app."""

from __future__ import annotations

import pytest

from resumes.models import Achievement, Education, Experience, Profile, Skill


@pytest.mark.django_db
def test_user_can_edit_every_section_and_export_pdf(client):
    client.get("/resume/edit/")
    profile = Profile.objects.get()
    client.post(
        "/resume/personal/save/",
        {
            "full_name": "Ada Lovelace",
            "email": "ada@example.com",
            "phone": "555-0100",
            "location": "London",
            "linkedin_url": "https://linkedin.com/in/ada",
            "portfolio_url": "https://ada.example.com",
        },
    )
    client.post(
        "/resume/summary/save/",
        {
            "professional_summary": (
                "Builder of practical analytical systems with a record of shipping reliable "
                "tools for technical and non-technical teams."
            )
        },
    )
    client.post("/resume/experience/add/")
    experience = Experience.objects.get(profile=profile)
    client.post(
        f"/resume/experience/{experience.id}/save/",
        {
            "company": "Analytical Engines",
            "title": "Engineer",
            "location": "Remote",
            "start_date": "2024-01-01",
            "end_date": "",
            "current_role": "on",
        },
    )
    client.post(f"/resume/experience/{experience.id}/achievement/add/")
    achievement = Achievement.objects.get(experience=experience)
    client.post(
        f"/resume/achievement/{achievement.id}/save/",
        {"text": "Built 3 reporting tools that reduced manual reconciliation by 40%."},
    )
    Education.objects.create(profile=profile, institution="University", degree="BS", field="Math", order=1)
    Skill.objects.create(profile=profile, name="Python", category="technical", proficiency=5, order=1)
    Skill.objects.create(profile=profile, name="Django", category="technical", proficiency=5, order=2)
    Skill.objects.create(profile=profile, name="Analysis", category="technical", proficiency=4, order=3)

    response = client.get("/resume/export/?format=pdf")

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF-")
