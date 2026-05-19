"""Tests for rate-limit key helpers and shared cache."""

from __future__ import annotations

import pytest
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.management import call_command
from django.test import RequestFactory, override_settings

from resumes.rate_limit import client_ip_for_rate_limit, session_rate_key


def _request_with_session(*, save: bool) -> object:
    request = RequestFactory().get("/")
    SessionMiddleware(lambda req: None).process_request(request)
    if save:
        request.session.save()
    return request


def test_client_ip_prefers_x_forwarded_for_first_hop():
    request = RequestFactory().get("/")
    request.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.10, 10.0.0.1"
    request.META["REMOTE_ADDR"] = "10.0.0.1"

    assert client_ip_for_rate_limit(request) == "203.0.113.10"


def test_client_ip_falls_back_to_remote_addr():
    request = RequestFactory().get("/")
    request.META["REMOTE_ADDR"] = "198.51.100.4"

    assert client_ip_for_rate_limit(request) == "198.51.100.4"


@pytest.mark.django_db
def test_session_rate_key_uses_session_when_present():
    request = _request_with_session(save=True)

    assert session_rate_key("export", request) == request.session.session_key


@pytest.mark.django_db
def test_session_rate_key_uses_client_ip_without_session():
    request = _request_with_session(save=False)
    request.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.55"

    assert session_rate_key("export", request) == "203.0.113.55"


@pytest.mark.django_db
@override_settings(RATELIMIT_ENABLE=True)
def test_export_rate_limit_uses_database_cache(client, profile, settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "test_rate_limit_cache",
        }
    }
    call_command("createcachetable", verbosity=0)

    session = client.session
    session.save()
    profile.session_key = session.session_key
    profile.save()

    for _ in range(30):
        assert client.get("/resume/export/?format=txt").status_code == 200

    assert client.get("/resume/export/?format=txt").status_code == 403
