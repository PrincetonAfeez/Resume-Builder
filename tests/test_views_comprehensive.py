"""Additional view coverage for CRUD, ownership, and edge cases."""

from __future__ import annotations

import pytest

from resumes.models import Achievement, Education, Experience, Profile, Skill


@pytest.mark.django_db
def test_summary_save_updates_profile(client):
    client.get("/resume/edit/")
    profile = Profile.objects.get()

    response = client.post(
        "/resume/summary/save/",
        {"professional_summary": "Updated summary text."},
        HTTP_HX_REQUEST="true",
    )
    profile.refresh_from_db()

    assert response.status_code == 200
    assert response["HX-Trigger"] == "resume:saved"
    assert profile.professional_summary == "Updated summary text."


@pytest.mark.django_db
def test_skill_delete_and_move(client):
    client.get("/resume/edit/")
    profile = Profile.objects.get()
    client.post("/resume/skill/add/", HTTP_HX_REQUEST="true")
    skill = Skill.objects.filter(profile=profile).order_by("-order").first()
    assert skill is not None

    move = client.post(
        f"/resume/skill/{skill.id}/move/",
        {"direction": "up"},
        HTTP_HX_REQUEST="true",
    )
    assert move.status_code == 200

    delete = client.post(f"/resume/skill/{skill.id}/delete/", HTTP_HX_REQUEST="true")
    assert delete.status_code == 200
    assert not Skill.objects.filter(pk=skill.pk).exists()


@pytest.mark.django_db
def test_education_delete_and_move(client):
    client.get("/resume/edit/")
    profile = Profile.objects.get()
    client.post("/resume/education/add/", HTTP_HX_REQUEST="true")
    education = Education.objects.filter(profile=profile).order_by("-order").first()
    assert education is not None

    move = client.post(
        f"/resume/education/{education.id}/move/",
        {"direction": "down"},
        HTTP_HX_REQUEST="true",
    )
    assert move.status_code == 200

    delete = client.post(f"/resume/education/{education.id}/delete/", HTTP_HX_REQUEST="true")
    assert delete.status_code == 200
    assert not Education.objects.filter(pk=education.pk).exists()


@pytest.mark.django_db
def test_achievement_add_move_delete(client):
    client.get("/resume/edit/")
    experience = Experience.objects.create(profile=Profile.objects.get(), company="Beta", order=50)

    add = client.post(f"/resume/experience/{experience.id}/achievement/add/", HTTP_HX_REQUEST="true")
    assert add.status_code == 200
    achievement = Achievement.objects.get(experience=experience)

    move = client.post(
        f"/resume/achievement/{achievement.id}/move/",
        {"direction": "down"},
        HTTP_HX_REQUEST="true",
    )
    assert move.status_code == 200

    delete = client.post(f"/resume/achievement/{achievement.id}/delete/", HTTP_HX_REQUEST="true")
    assert delete.status_code == 200
    assert not Achievement.objects.filter(pk=achievement.pk).exists()


@pytest.mark.django_db
def test_undo_without_snapshot_is_noop(client):
    client.get("/resume/edit/")
    profile = Profile.objects.get()
    profile.full_name = "Before Undo"
    profile.save()

    response = client.post("/resume/undo/", follow=True)
    profile.refresh_from_db()

    assert response.status_code == 200
    assert profile.full_name == "Before Undo"


@pytest.mark.django_db
def test_analyzer_persists_jd_text(client):
    client.get("/resume/edit/")
    profile = Profile.objects.get()

    response = client.post(
        "/resume/analyze/run/",
        {"jd_text": "Python Django PostgreSQL"},
        HTTP_HX_REQUEST="true",
    )
    profile.refresh_from_db()

    assert response.status_code == 200
    assert profile.jd_text == "Python Django PostgreSQL"
    assert b"match" in response.content.lower() or b"%" in response.content


@pytest.mark.django_db
def test_export_all_formats_content_types(client, bound_profile):
    cases = [
        ("pdf", "application/pdf", "resume.pdf"),
        ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "resume.docx"),
        ("txt", "text/plain; charset=utf-8", "resume.txt"),
    ]
    for fmt, content_type, filename in cases:
        response = client.get(f"/resume/export/?format={fmt}")
        assert response.status_code == 200
        assert response["Content-Type"] == content_type
        assert response["Content-Disposition"] == f'attachment; filename="{filename}"'


@pytest.mark.django_db
def test_foreign_experience_save_returns_404(client, bound_profile):
    other = Profile.objects.create(session_key="foreign")
    row = Experience.objects.create(profile=other, company="X", order=1)

    response = client.post(f"/resume/experience/{row.pk}/save/", {}, HTTP_HX_REQUEST="true")

    assert response.status_code == 404


@pytest.mark.django_db
def test_foreign_skill_delete_returns_404(client, bound_profile):
    other = Profile.objects.create(session_key="foreign")
    row = Skill.objects.create(profile=other, name="X", order=1)

    response = client.post(f"/resume/skill/{row.pk}/delete/", HTTP_HX_REQUEST="true")

    assert response.status_code == 404


@pytest.mark.django_db
def test_foreign_education_move_returns_404(client, bound_profile):
    other = Profile.objects.create(session_key="foreign")
    row = Education.objects.create(profile=other, institution="X", order=1)

    response = client.post(
        f"/resume/education/{row.pk}/move/",
        {"direction": "up"},
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 404
