"""Middleware for the resumes app."""

from __future__ import annotations

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from .services.profile import get_or_create_profile


class ProfileSessionMiddleware:
    """Ensure browser sessions have a profile before resume views run."""

    skip_prefixes = ("/admin/", "/static/", "/health/", "/favicon.ico")

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not request.path.startswith(self.skip_prefixes):
            request.resume_profile = get_or_create_profile(request)  # type: ignore[attr-defined]
        return self.get_response(request)
