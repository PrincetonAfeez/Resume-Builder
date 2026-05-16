"""Tests for the export services for the resumes app."""

from __future__ import annotations

import pytest

from resumes.models import Theme
from resumes.services.resume_export import (
    ExportFormat,
    build_resume_context,
    export_resume,
    export_txt,
    pdf_uses_weasyprint,
    weasyprint_runtime_available,
)


@pytest.mark.django_db
def test_build_resume_context_invalid_theme_falls_back(profile):
    profile.chosen_theme = Theme.MINIMAL
    profile.save()

    context = build_resume_context(profile, "not-a-theme")

    assert context["theme"] == Theme.MINIMAL


@pytest.mark.django_db
def test_export_resume_rejects_unknown_format(profile):
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_resume(profile, "classic", "rtf")  # type: ignore[arg-type]


@pytest.mark.django_db
def test_export_txt_includes_major_sections(profile):
    text = export_txt(build_resume_context(profile, "classic"))

    assert "Ada Lovelace" in text
    assert "SUMMARY" in text
    assert "EXPERIENCE" in text
    assert "EDUCATION" in text
    assert "SKILLS" in text
    assert "CERTIFICATIONS" in text
    assert "40%" in text


@pytest.mark.django_db
@pytest.mark.parametrize("theme", list(Theme.values))
def test_pdf_and_docx_export_for_each_theme(profile, theme: str):
    pdf = export_resume(profile, theme, ExportFormat.PDF)
    docx = export_resume(profile, theme, ExportFormat.DOCX)

    assert pdf.startswith(b"%PDF-")
    assert docx.startswith(b"PK")


@pytest.mark.django_db
def test_fallback_pdf_is_valid_without_weasyprint_metadata(profile):
    from resumes.services.resume_export import _fallback_pdf

    pdf = _fallback_pdf(build_resume_context(profile, "classic"))

    assert pdf.startswith(b"%PDF-")
    assert not pdf_uses_weasyprint(pdf)
    assert b"Ada Lovelace" in pdf or b"Resume" in pdf


@pytest.mark.weasyprint
@pytest.mark.django_db
def test_production_pdf_uses_weasyprint_runtime(profile):
    if not weasyprint_runtime_available():
        pytest.skip("WeasyPrint native runtime not available on this host")

    pdf = export_resume(profile, "classic", ExportFormat.PDF)

    assert pdf_uses_weasyprint(pdf)
    assert len(pdf) > 1500
