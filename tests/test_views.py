"""Tests for the views for the resumes app."""

from __future__ import annotations

from io import StringIO

import pytest
from django.contrib.sessions.models import Session
from django.core.management import call_command
from django.test import override_settings

from resumes.models import Achievement, Education, Experience, Profile, Skill


@pytest.mark.django_db
def test_anonymous_session_creates_one_profile(client):
    response = client.get("/resume/edit/")
    assert response.status_code == 200
    assert Profile.objects.count() == 1

    client.get("/resume/edit/")
    assert Profile.objects.count() == 1


@pytest.mark.django_db
def test_htmx_personal_save_updates_profile(client):
    client.get("/resume/edit/")
    profile = Profile.objects.get()

    response = client.post(
        "/resume/personal/save/",
        {
            "full_name": "Ada Lovelace",
            "email": "ada@example.com",
            "phone": "555-0100",
            "location": "London",
            "linkedin_url": "",
            "portfolio_url": "",
        },
        HTTP_HX_REQUEST="true",
    )
    profile.refresh_from_db()

    assert response.status_code == 200
    assert profile.full_name == "Ada Lovelace"
    assert b'hx-swap-oob="outerHTML"' in response.content


@pytest.mark.django_db
def test_add_save_move_and_delete_experience(client):
    client.get("/resume/edit/")
    profile = Profile.objects.get()

    add_response = client.post("/resume/experience/add/", HTTP_HX_REQUEST="true")
    experience = Experience.objects.get(profile=profile)
    save_response = client.post(
        f"/resume/experience/{experience.id}/save/",
        {
            "company": "Analytical Engines",
            "title": "Engineer",
            "location": "Remote",
            "start_date": "2024-01-01",
            "end_date": "",
            "current_role": "on",
        },
        HTTP_HX_REQUEST="true",
    )

    assert add_response.status_code == 200
    assert save_response.status_code == 200
    experience.refresh_from_db()
    assert experience.current_role is True

    Experience.objects.create(profile=profile, company="Earlier", order=2)
    move_response = client.post(
        f"/resume/experience/{experience.id}/move/",
        {"direction": "down"},
        HTTP_HX_REQUEST="true",
    )
    assert move_response.status_code == 200

    delete_response = client.post(f"/resume/experience/{experience.id}/delete/", HTTP_HX_REQUEST="true")
    assert delete_response.status_code == 200
    assert not Experience.objects.filter(id=experience.id).exists()


@pytest.mark.django_db
def test_achievement_quality_panel(client):
    client.get("/resume/edit/")
    profile = Profile.objects.get()
    experience = Experience.objects.create(profile=profile, company="Acme", order=1)
    achievement = Achievement.objects.create(experience=experience, text="Responsible for reports", order=1)

    response = client.get(f"/resume/action-verbs/{achievement.id}/", HTTP_HX_REQUEST="true")

    assert response.status_code == 200
    assert b"Delivered" in response.content


@pytest.mark.django_db
def test_education_skill_certification_flows(client):
    client.get("/resume/edit/")
    profile = Profile.objects.get()

    assert client.post("/resume/education/add/", HTTP_HX_REQUEST="true").status_code == 200
    education = Education.objects.get(profile=profile)
    save_response = client.post(
        f"/resume/education/{education.id}/save/",
        {
            "institution": "University",
            "degree": "BS",
            "field": "Computer Science",
            "start_date": "2020-01-01",
            "end_date": "2024-01-01",
            "gpa": "",
            "notes": "",
        },
        HTTP_HX_REQUEST="true",
    )
    assert save_response.status_code == 200
    assert save_response["HX-Trigger"] == "resume:saved"
    assert b'name="institution"' in save_response.content
    assert b'name="degree"' in save_response.content

    invalid_education = client.post(
        f"/resume/education/{education.id}/save/",
        {
            "institution": "University",
            "degree": "BS",
            "field": "Computer Science",
            "start_date": "2024-06-01",
            "end_date": "2020-01-01",
            "gpa": "",
            "notes": "",
        },
        HTTP_HX_REQUEST="true",
    )
    assert invalid_education.status_code == 200
    assert invalid_education["HX-Trigger"] == "resume:invalid"
    assert b'name="institution"' in invalid_education.content
    assert b'name="degree"' in invalid_education.content

    assert client.post("/resume/skill/add/", HTTP_HX_REQUEST="true").status_code == 200
    skill = Skill.objects.get(profile=profile)
    assert (
        client.post(
            f"/resume/skill/{skill.id}/save/",
            {"name": "Python", "category": "technical", "proficiency": "5"},
            HTTP_HX_REQUEST="true",
        ).status_code
        == 200
    )


@pytest.mark.django_db
def test_exports_and_analyzer_endpoints(client, profile):
    session = client.session
    session.save()
    profile.session_key = session.session_key
    profile.save()

    pdf_response = client.get("/resume/export/?format=pdf")
    docx_response = client.get("/resume/export/?format=docx")
    txt_response = client.get("/resume/export/?format=txt")
    analysis_response = client.post(
        "/resume/analyze/run/",
        {"jd_text": "Python Django reporting automation"},
        HTTP_HX_REQUEST="true",
    )

    assert pdf_response.content.startswith(b"%PDF-")
    assert docx_response["Content-Type"].startswith(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert b"Ada Lovelace" in txt_response.content
    assert b"Present" in analysis_response.content


@pytest.mark.django_db
def test_first_visit_notice_shows_once(client):
    response = client.get("/resume/edit/")

    assert response.status_code == 200
    assert b"Your resume lives in this browser session" in response.content

    repeat = client.get("/resume/edit/")
    assert b"Your resume lives in this browser session" not in repeat.content


@pytest.mark.django_db
@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
    RATELIMIT_ENABLE=True,
)
def test_export_rate_limit_blocks_after_threshold(client, profile):
    session = client.session
    session.save()
    profile.session_key = session.session_key
    profile.save()

    for _ in range(30):
        assert client.get("/resume/export/?format=txt").status_code == 200

    blocked = client.get("/resume/export/?format=txt")
    assert blocked.status_code == 403


@pytest.mark.django_db
def test_prune_stale_profiles_command(client):
    client.get("/resume/edit/")
    assert Session.objects.count() == 1
    Session.objects.all().delete()

    from resumes.services.profile import prune_stale_profiles

    assert prune_stale_profiles() == 1


@pytest.mark.django_db
def test_prune_stale_profiles_management_command(client):
    client.get("/resume/edit/")
    Session.objects.all().delete()

    out = StringIO()
    call_command("prune_stale_profiles", stdout=out)
    assert "Deleted 1 stale profile" in out.getvalue()
