"""Tests for ProfileSessionMiddleware."""

from __future__ import annotations

import pytest
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpResponse
from django.test import RequestFactory

from resumes.middleware import ProfileSessionMiddleware
from resumes.models import Profile


def _middleware_response() -> ProfileSessionMiddleware:
    return ProfileSessionMiddleware(lambda request: HttpResponse("ok"))


@pytest.mark.django_db
@pytest.mark.parametrize(
    "path",
    ["/admin/", "/static/app.css", "/health/", "/favicon.ico"],
)
def test_middleware_skips_profile_for_excluded_paths(path: str):
    request = RequestFactory().get(path)
    request.session = SessionStore()

    response = _middleware_response()(request)

    assert response.status_code == 200
    assert not hasattr(request, "resume_profile")


@pytest.mark.django_db
def test_middleware_attaches_profile_for_resume_paths():
    request = RequestFactory().get("/resume/edit/")
    request.session = SessionStore()

    _middleware_response()(request)

    assert hasattr(request, "resume_profile")
    assert isinstance(request.resume_profile, Profile)
    assert request.resume_profile.session_key == request.session.session_key


@pytest.mark.django_db
def test_middleware_reuses_existing_profile_for_session():
    request = RequestFactory().get("/resume/edit/")
    request.session = SessionStore()
    request.session.save()
    existing = Profile.objects.create(session_key=request.session.session_key)

    _middleware_response()(request)

    assert request.resume_profile.pk == existing.pk
