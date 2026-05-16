"""Tests for the services for the resumes app."""

from __future__ import annotations

import pytest

from resumes.models import Achievement, Experience
from resumes.services.analysis import (
    action_verb_suggestions,
    analyze_job_description,
    check_bullet_quality,
    completeness_score,
    replace_weak_opener,
)
from resumes.services.profile import capture_undo_snapshot, restore_profile_snapshot
from resumes.services.resume_export import ExportFormat, build_resume_context, export_resume


@pytest.mark.django_db
def test_completeness_score(profile):
    result = completeness_score(profile)

    assert result.score >= 90
    assert any(label == "Has three skills" and passed for label, _points, passed in result.breakdown)


def test_bullet_quality_and_verb_replacement():
    warnings = check_bullet_quality("Responsible for platform work")

    assert {warning.code for warning in warnings} >= {"weak_opener", "no_quantification"}
    assert action_verb_suggestions("Responsible for platform work")
    assert replace_weak_opener("Responsible for platform work", "Delivered") == "Delivered platform work"


@pytest.mark.django_db
def test_keyword_analysis(profile):
    analysis = analyze_job_description(
        profile,
        "We need Python and Django experience with automated reporting and reliable systems.",
    )

    assert analysis.match_percentage > 0
    assert "python" in analysis.present


@pytest.mark.django_db
def test_keyword_analysis_empty_job_description(profile):
    analysis = analyze_job_description(profile, "")

    assert analysis.match_percentage == 0
    assert analysis.present == []
    assert analysis.missing == []


@pytest.mark.django_db
def test_exports(profile):
    context = build_resume_context(profile, "classic")
    txt = export_resume(profile, "classic", ExportFormat.TXT)
    docx = export_resume(profile, "modern", ExportFormat.DOCX)
    pdf = export_resume(profile, "minimal", ExportFormat.PDF)

    assert context["theme"] == "classic"
    assert b"Ada Lovelace" in txt
    assert docx.startswith(b"PK")
    assert pdf.startswith(b"%PDF-")


@pytest.mark.django_db
def test_restore_profile_snapshot(rf, profile):
    request = rf.get("/resume/edit/")
    request.session = {"undo_snapshot": None, "modified": False}
    capture_undo_snapshot(request, profile)
    profile.full_name = "Changed Name"
    profile.save()

    restore_profile_snapshot(profile, request.session["undo_snapshot"])
    profile.refresh_from_db()

    assert profile.full_name == "Ada Lovelace"


@pytest.mark.django_db
def test_capture_undo_snapshot_ignores_unsaved_form_state(rf, profile):
    request = rf.get("/resume/edit/")
    request.session = {}
    profile.full_name = "Changed In Memory"

    capture_undo_snapshot(request, profile)

    assert request.session["undo_snapshot"]["profile"]["full_name"] == "Ada Lovelace"


@pytest.mark.django_db
def test_restore_recreates_related_rows(profile):
    snapshot = {
        "profile": {"full_name": "Grace Hopper"},
        "experiences": [
            {
                "fields": {"company": "Navy", "title": "Admiral", "order": 1, "current_role": False},
                "achievements": [{"text": "Built 1 compiler.", "order": 1}],
            }
        ],
        "education": [],
        "skills": [],
        "certifications": [],
    }

    restore_profile_snapshot(profile, snapshot)

    assert profile.experiences.count() == 1
    assert Experience.objects.get(profile=profile).achievements.count() == 1
    assert Achievement.objects.get(experience__profile=profile).text == "Built 1 compiler."
