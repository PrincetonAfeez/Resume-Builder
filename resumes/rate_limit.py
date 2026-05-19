"""Rate-limit key helpers for django-ratelimit."""

from __future__ import annotations

from django.http import HttpRequest


def client_ip_for_rate_limit(request: HttpRequest) -> str:
    """Client IP for rate limiting when no session key exists."""
    # Trust X-Forwarded-For only behind a platform proxy (e.g. Railway) that injects it.
    # If the app is reached directly, clients could spoof this header; use REMOTE_ADDR then.
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "anonymous")


def session_rate_key(_group: str, request: HttpRequest) -> str:
    """Per-session rate limit; fall back to client IP behind proxies."""
    if request.session.session_key:
        return request.session.session_key
    return client_ip_for_rate_limit(request)
