"""Project URL configuration."""

from __future__ import annotations

from django.contrib import admin
from django.http import HttpRequest, JsonResponse
from django.shortcuts import redirect
from django.urls import include, path


def home(_request: HttpRequest):
    return redirect("resumes:edit")


def health(_request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("", include("resumes.urls")),
]
