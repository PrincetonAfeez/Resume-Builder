"""Tests for the profile services for the resumes app."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.test import RequestFactory
from django.utils import timezone

from resumes.models import Profile, Skill
from resumes.services.profile import (
    capture_undo_snapshot,
    get_or_create_profile,
    move_ordered_item,
    next_order,
    prune_stale_profiles,
    serialize_profile,
)


@pytest.mark.django_db
def test_get_or_create_profile_creates_session_key():
    request = RequestFactory().get("/resume/edit/")
    request.session = SessionStore()

    profile = get_or_create_profile(request)

    assert request.session.session_key
    assert profile.session_key == request.session.session_key


@pytest.mark.django_db
def test_next_order_increments(profile):
    assert next_order(profile.skills.all()) == 4
    Skill.objects.create(profile=profile, name="Rust", order=4)
    assert next_order(profile.skills.all()) == 5


@pytest.mark.django_db
def test_move_ordered_item_swaps_and_respects_bounds(profile):
    first = Skill.objects.get(profile=profile, name="Python")
    second = Skill.objects.get(profile=profile, name="Django")
    original_first_order = first.order

    second_order_before = second.order
    move_ordered_item(first, profile.skills.all(), "down")
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.order == second_order_before
    assert second.order == original_first_order

    move_ordered_item(first, profile.skills.all(), "up")
    first.refresh_from_db()
    assert first.order == original_first_order

    move_ordered_item(first, profile.skills.all(), "invalid")
    move_ordered_item(first, profile.skills.all(), "up")
    move_ordered_item(first, profile.skills.all(), "up")


@pytest.mark.django_db
def test_serialize_profile_includes_nested_achievements(profile):
    payload = serialize_profile(profile)

    assert payload["profile"]["full_name"] == "Ada Lovelace"
    assert len(payload["experiences"]) == 1
    assert payload["experiences"][0]["achievements"]
    assert payload["skills"]
    assert payload["certifications"]


@pytest.mark.django_db
def test_prune_keeps_profiles_with_active_sessions(profile):
    Session.objects.create(
        session_key=profile.session_key,
        session_data=SessionStore().encode({}),
        expire_date=timezone.now() + timedelta(days=30),
    )

    assert prune_stale_profiles() == 0
    assert Profile.objects.filter(pk=profile.pk).exists()


@pytest.mark.django_db
def test_capture_undo_snapshot_persists_in_session(rf, profile):
    request = rf.get("/resume/edit/")
    request.session = {}

    capture_undo_snapshot(request, profile)
    profile.full_name = "Changed"
    profile.save()

    assert request.session["undo_snapshot"]["profile"]["full_name"] == "Ada Lovelace"


@pytest.mark.django_db
def test_prune_deletes_only_orphan_profiles(profile):
    orphan = Profile.objects.create(session_key="orphan-session")
    Session.objects.create(
        session_key=profile.session_key,
        session_data=SessionStore().encode({}),
        expire_date=timezone.now() + timedelta(days=30),
    )

    deleted = prune_stale_profiles()

    assert deleted == 1
    assert Profile.objects.filter(pk=profile.pk).exists()
    assert not Profile.objects.filter(pk=orphan.pk).exists()
