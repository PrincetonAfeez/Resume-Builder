"""Tests that URL patterns resolve."""

from __future__ import annotations

import pytest
from django.urls import reverse


@pytest.mark.parametrize(
    "name",
    [
        "resumes:edit",
        "resumes:start_over",
        "resumes:undo",
        "resumes:save_personal",
        "resumes:save_summary",
        "resumes:save_theme",
        "resumes:add_experience",
        "resumes:export",
        "resumes:analyze",
        "resumes:run_analyzer",
    ],
)
def test_named_urls_resolve(name: str):
    assert reverse(name).startswith("/")


def test_urls_with_pk_kwargs_resolve():
    assert reverse("resumes:save_experience", kwargs={"pk": 1}) == "/resume/experience/1/save/"
    assert reverse("resumes:add_achievement", kwargs={"experience_id": 2}) == "/resume/experience/2/achievement/add/"
    assert reverse("resumes:action_verbs", kwargs={"achievement_id": 3}) == "/resume/action-verbs/3/"
