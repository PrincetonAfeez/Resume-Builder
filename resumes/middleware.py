"""Middleware for the resumes app."""

from __future__ import annotations

from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from .services.profile import get_or_create_profile


class ProfileSessionMiddleware:
    """Attach a session profile only on resume routes (avoids bot noise on unknown paths)."""

    resume_prefix = "/resume/"

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def _should_attach_profile(self, path: str) -> bool:
        return path.startswith(self.resume_prefix)

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if self._should_attach_profile(request.path):
            request.resume_profile = get_or_create_profile(request)  # type: ignore[attr-defined]
        return self.get_response(request)


class SecurityHeadersMiddleware:
    """Production security headers (CSP, Permissions-Policy) not covered by Django defaults."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        csp = getattr(settings, "CONTENT_SECURITY_POLICY", None)
        if csp:
            response["Content-Security-Policy"] = csp
        permissions_policy = getattr(settings, "PERMISSIONS_POLICY", None)
        if permissions_policy:
            response["Permissions-Policy"] = permissions_policy
        return response
