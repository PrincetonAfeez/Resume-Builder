"""Tests for the extended views for the resumes app."""

from __future__ import annotations

import pytest
from django.test import override_settings

from resumes.models import Achievement, Certification, Experience, Profile


@pytest.mark.django_db
def test_home_redirects_to_editor(client):
    assert client.get("/").status_code == 302
    assert client.get("/").url == "/resume/edit/"


@pytest.mark.django_db
def test_health_endpoint(client):
    response = client.get("/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_analyze_page_renders(client):
    response = client.get("/resume/analyze/")

    assert response.status_code == 200
    assert b"JD Analyzer" in response.content


@pytest.mark.django_db
def test_undo_restores_snapshot(client):
    client.get("/resume/edit/")
    profile = Profile.objects.get(session_key=client.session.session_key)
    profile.full_name = "Ada Lovelace"
    profile.email = "ada@example.com"
    profile.phone = "555-0100"
    profile.location = "London"
    profile.save()

    client.post(
        "/resume/personal/save/",
        {
            "full_name": "Changed Name",
            "email": "ada@example.com",
            "phone": "555-0100",
            "location": "London",
            "linkedin_url": "",
            "portfolio_url": "",
        },
        HTTP_HX_REQUEST="true",
    )
    profile.refresh_from_db()
    assert profile.full_name == "Changed Name"
    assert "undo_snapshot" in client.session

    client.post("/resume/undo/", follow=True)
    profile.refresh_from_db()
    assert profile.full_name == "Ada Lovelace"


@pytest.mark.django_db
def test_start_over_creates_fresh_profile(client, bound_profile):
    original_id = bound_profile.id
    client.get("/resume/edit/")
    client.post("/resume/start-over/", follow=True)

    current = Profile.objects.get(session_key=client.session.session_key)
    assert current.pk != original_id
    assert Profile.objects.filter(pk=original_id).exists()


@pytest.mark.django_db
def test_theme_save_updates_preview(client):
    client.get("/resume/edit/")
    profile = Profile.objects.get()

    response = client.post(
        "/resume/theme/save/",
        {"chosen_theme": "modern", "accent_color": "emerald", "font_pairing": "serif"},
        HTTP_HX_REQUEST="true",
    )
    profile.refresh_from_db()

    assert response.status_code == 200
    assert profile.chosen_theme == "modern"
    assert b"resume-theme modern" in response.content


@pytest.mark.django_db
def test_achievement_replace_weak_opener(client):
    client.get("/resume/edit/")
    experience = Experience.objects.create(profile=Profile.objects.get(), company="Acme", order=99)
    achievement = Achievement.objects.create(experience=experience, text="Responsible for billing", order=1)

    response = client.post(
        f"/resume/achievement/{achievement.id}/save/",
        {"text": "Responsible for billing", "replace_with": "Delivered"},
        HTTP_HX_REQUEST="true",
    )
    achievement.refresh_from_db()

    assert response.status_code == 200
    assert achievement.text == "Delivered billing"


@pytest.mark.django_db
def test_certification_crud_flow(client):
    client.get("/resume/edit/")
    profile = Profile.objects.get()

    assert client.post("/resume/certification/add/", HTTP_HX_REQUEST="true").status_code == 200
    certification = Certification.objects.get(profile=profile)
    save = client.post(
        f"/resume/certification/{certification.id}/save/",
        {
            "name": "PMP",
            "issuing_body": "PMI",
            "date_earned": "2020-01-01",
            "expiry": "",
            "credential_id": "123",
        },
        HTTP_HX_REQUEST="true",
    )
    delete = client.post(f"/resume/certification/{certification.id}/delete/", HTTP_HX_REQUEST="true")

    assert save.status_code == 200
    assert delete.status_code == 200
    assert not Certification.objects.filter(pk=certification.pk).exists()


@pytest.mark.django_db
def test_export_invalid_format_returns_400(client, bound_profile):
    response = client.get("/resume/export/?format=rtf")

    assert response.status_code == 400


@pytest.mark.django_db
def test_export_sets_content_disposition(client, bound_profile):
    response = client.get("/resume/export/?format=txt")

    assert response.status_code == 200
    assert response["Content-Disposition"] == 'attachment; filename="resume.txt"'


@pytest.mark.django_db
def test_foreign_achievement_returns_404(client, bound_profile):
    other = Profile.objects.create(session_key="other")
    experience = Experience.objects.create(profile=other, company="Other Co", order=1)
    achievement = Achievement.objects.create(experience=experience, text="Secret", order=1)

    response = client.get(f"/resume/action-verbs/{achievement.id}/", HTTP_HX_REQUEST="true")

    assert response.status_code == 404


@pytest.mark.django_db
@override_settings(RATELIMIT_ENABLE=True)
def test_analyzer_rate_limit(client, bound_profile, locmem_cache):
    for _ in range(30):
        assert (
            client.post(
                "/resume/analyze/run/",
                {"jd_text": "Python Django"},
                HTTP_HX_REQUEST="true",
            ).status_code
            == 200
        )

    blocked = client.post(
        "/resume/analyze/run/",
        {"jd_text": "Python Django"},
        HTTP_HX_REQUEST="true",
    )
    assert blocked.status_code == 403


@pytest.mark.django_db
def test_personal_save_sets_htmx_trigger(client):
    client.get("/resume/edit/")

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

    assert response["HX-Trigger"] == "resume:saved"


@pytest.mark.django_db
def test_invalid_achievement_save_sets_invalid_trigger(client):
    client.get("/resume/edit/")
    experience = Experience.objects.create(profile=Profile.objects.get(), company="Acme", order=98)
    achievement = Achievement.objects.create(experience=experience, text="Valid bullet", order=1)

    response = client.post(
        f"/resume/achievement/{achievement.id}/save/",
        {"text": "x" * 181},
        HTTP_HX_REQUEST="true",
    )
    achievement.refresh_from_db()

    assert response.status_code == 200
    assert response["HX-Trigger"] == "resume:invalid"
    assert achievement.text == "Valid bullet"
    assert b"180" in response.content


@pytest.mark.django_db
def test_invalid_experience_save_sets_invalid_trigger(client):
    client.get("/resume/edit/")
    client.post("/resume/experience/add/", HTTP_HX_REQUEST="true")
    experience = Experience.objects.get()

    response = client.post(
        f"/resume/experience/{experience.id}/save/",
        {
            "company": "Acme",
            "title": "Engineer",
            "location": "",
            "start_date": "2024-06-01",
            "end_date": "2024-01-01",
            "current_role": "",
        },
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    assert response["HX-Trigger"] == "resume:invalid"
    experience.refresh_from_db()
    assert experience.company != "Acme" or not experience.company
