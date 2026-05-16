"""Profile services for the resumes app."""

from __future__ import annotations

from typing import Any, Protocol, TypeVar

from django.contrib.sessions.models import Session
from django.db import transaction
from django.db.models import Max, Model, QuerySet
from django.http import HttpRequest
from django.utils import timezone

from resumes.models import (
    Achievement,
    Certification,
    Education,
    Experience,
    Profile,
    Skill,
)


class ProfileRequest(Protocol):
    session: Any


OrderedModel = TypeVar("OrderedModel", bound=Model)


PROFILE_FIELDS = [
    "full_name",
    "email",
    "phone",
    "location",
    "linkedin_url",
    "portfolio_url",
    "professional_summary",
    "chosen_theme",
    "accent_color",
    "font_pairing",
    "jd_text",
    "first_visit_notice_seen",
]


def get_or_create_profile(request: ProfileRequest) -> Profile:
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    profile, _created = Profile.objects.get_or_create(session_key=session_key)
    return profile


def next_order(queryset: QuerySet[Any]) -> int:
    """Return the next order value; call inside transaction.atomic() before create."""

    locked = queryset.select_for_update()
    current = locked.aggregate(max_order=Max("order"))["max_order"]
    return int(current or 0) + 1


def move_ordered_item(item: Any, siblings: QuerySet[Any], direction: str) -> None:
    if direction not in {"up", "down"}:
        return

    ordered = list(siblings.order_by("order", "id"))
    ids = [obj.id for obj in ordered]
    try:
        index = ids.index(item.id)
    except ValueError:
        return

    swap_index = index - 1 if direction == "up" else index + 1
    if swap_index < 0 or swap_index >= len(ordered):
        return

    other = ordered[swap_index]
    item.order, other.order = other.order, item.order
    item.save(update_fields=["order", "updated_at"])
    other.save(update_fields=["order", "updated_at"])


def capture_undo_snapshot(request: HttpRequest, profile: Profile) -> None:
    """Persist pre-change state; reload from DB so bound forms cannot pollute the snapshot."""

    fresh = Profile.objects.get(pk=profile.pk)
    request.session["undo_snapshot"] = serialize_profile(fresh)
    if hasattr(request.session, "modified"):
        request.session.modified = True


def serialize_profile(profile: Profile) -> dict[str, Any]:
    data: dict[str, Any] = {
        "profile": {field: getattr(profile, field) for field in PROFILE_FIELDS},
        "experiences": [],
        "education": [],
        "skills": [],
        "certifications": [],
    }
    for experience in profile.experiences.prefetch_related("achievements").all():
        data["experiences"].append(
            {
                "fields": _model_fields(
                    experience,
                    ["company", "title", "location", "start_date", "end_date", "current_role", "order"],
                ),
                "achievements": [
                    _model_fields(achievement, ["text", "order"]) for achievement in experience.achievements.all()
                ],
            }
        )
    data["education"] = [
        _model_fields(item, ["institution", "degree", "field", "start_date", "end_date", "gpa", "notes", "order"])
        for item in profile.education.all()
    ]
    data["skills"] = [
        _model_fields(item, ["name", "category", "proficiency", "order"]) for item in profile.skills.all()
    ]
    data["certifications"] = [
        _model_fields(item, ["name", "issuing_body", "date_earned", "expiry", "credential_id", "order"])
        for item in profile.certifications.all()
    ]
    return data


def restore_profile_snapshot(profile: Profile, snapshot: dict[str, Any]) -> None:
    with transaction.atomic():
        for field, value in snapshot.get("profile", {}).items():
            if field in PROFILE_FIELDS:
                setattr(profile, field, value)
        profile.save()

        profile.experiences.all().delete()
        profile.education.all().delete()
        profile.skills.all().delete()
        profile.certifications.all().delete()

        for experience_data in snapshot.get("experiences", []):
            achievements = experience_data.get("achievements", [])
            experience = Experience.objects.create(profile=profile, **experience_data.get("fields", {}))
            for achievement_data in achievements:
                Achievement.objects.create(experience=experience, **achievement_data)

        for item_data in snapshot.get("education", []):
            Education.objects.create(profile=profile, **item_data)
        for item_data in snapshot.get("skills", []):
            Skill.objects.create(profile=profile, **item_data)
        for item_data in snapshot.get("certifications", []):
            Certification.objects.create(profile=profile, **item_data)


def prune_stale_profiles() -> int:
    active_session_keys = set(
        Session.objects.filter(expire_date__gt=timezone.now()).values_list("session_key", flat=True)
    )
    queryset = Profile.objects.exclude(session_key__in=active_session_keys)
    count = queryset.count()
    queryset.delete()
    return count


def _model_fields(instance: Any, fields: list[str]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field in fields:
        value = getattr(instance, field)
        payload[field] = value.isoformat() if hasattr(value, "isoformat") else value
    return payload
