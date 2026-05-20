"""Tests for ProfileSessionMiddleware and SecurityHeadersMiddleware."""

from __future__ import annotations

import pytest
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpResponse
from django.test import RequestFactory, override_settings

from resumes.middleware import ProfileSessionMiddleware, SecurityHeadersMiddleware
from resumes.models import Profile


def _profile_middleware() -> ProfileSessionMiddleware:
    return ProfileSessionMiddleware(lambda request: HttpResponse("ok"))


@pytest.mark.django_db
@pytest.mark.parametrize(
    "path",
    ["/admin/", "/static/app.css", "/health/", "/favicon.ico", "/", "/wp-login.php", "/unknown"],
)
def test_middleware_skips_profile_for_non_resume_paths(path: str):
    request = RequestFactory().get(path)
    request.session = SessionStore()

    response = _profile_middleware()(request)

    assert response.status_code == 200
    assert not hasattr(request, "resume_profile")


@pytest.mark.django_db
def test_middleware_does_not_create_profile_on_unknown_paths():
    request = RequestFactory().get("/wp-admin/setup-config.php")
    request.session = SessionStore()

    _profile_middleware()(request)

    assert not hasattr(request, "resume_profile")
    assert Profile.objects.count() == 0


@pytest.mark.django_db
def test_middleware_attaches_profile_for_resume_paths():
    request = RequestFactory().get("/resume/edit/")
    request.session = SessionStore()

    _profile_middleware()(request)

    assert hasattr(request, "resume_profile")
    assert isinstance(request.resume_profile, Profile)
    assert request.resume_profile.session_key == request.session.session_key


@pytest.mark.django_db
def test_middleware_reuses_existing_profile_for_session():
    request = RequestFactory().get("/resume/export/")
    request.session = SessionStore()
    request.session.save()
    existing = Profile.objects.create(session_key=request.session.session_key)

    _profile_middleware()(request)

    assert request.resume_profile.pk == existing.pk


@override_settings(
    CONTENT_SECURITY_POLICY="default-src 'self'",
    PERMISSIONS_POLICY="camera=()",
)
def test_security_headers_middleware_adds_configured_headers():
    request = RequestFactory().get("/health/")
    middleware = SecurityHeadersMiddleware(lambda req: HttpResponse("ok"))

    response = middleware(request)

    assert response["Content-Security-Policy"] == "default-src 'self'"
    assert response["Permissions-Policy"] == "camera=()"
