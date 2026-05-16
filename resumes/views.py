"""Views for the resumes app."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django_ratelimit.decorators import ratelimit

from .forms import (
    AchievementForm,
    CertificationForm,
    EducationForm,
    ExperienceForm,
    PersonalInfoForm,
    SkillForm,
    SummaryForm,
    ThemeForm,
)
from .models import Achievement, Certification, Education, Experience, Profile, Skill
from .services.analysis import (
    action_verb_suggestions,
    analyze_job_description,
    check_bullet_quality,
    completeness_score,
    replace_weak_opener,
)
from .services.profile import (
    capture_undo_snapshot,
    move_ordered_item,
    next_order,
    restore_profile_snapshot,
)
from .services.resume_export import CONTENT_TYPES, ExportFormat, build_resume_context, export_resume


def _profile(request: HttpRequest) -> Profile:
    return cast(Profile, request.resume_profile)  # type: ignore[attr-defined]


def _session_rate_key(_group: str, request: HttpRequest) -> str:
    return request.session.session_key or request.META.get("REMOTE_ADDR", "anonymous")


def _preview_context(profile: Profile) -> dict[str, Any]:
    context = build_resume_context(profile)
    context["score"] = completeness_score(profile)
    context["personal_form"] = PersonalInfoForm(instance=context["profile"])
    context["summary_form"] = SummaryForm(instance=context["profile"])
    context["theme_form"] = ThemeForm(instance=context["profile"])
    return context


def _render_with_preview(
    request: HttpRequest,
    template: str,
    context: dict[str, Any] | None = None,
    *,
    profile: Profile | None = None,
) -> HttpResponse:
    profile = profile or _profile(request)
    payload = _preview_context(profile)
    payload.update(context or {})
    payload["include_oob"] = True
    response = render(request, template, payload)
    response["HX-Trigger"] = "resume:saved"
    return response


def _render_list(request: HttpRequest, template: str, context: dict[str, Any] | None = None) -> HttpResponse:
    return _render_with_preview(request, template, context)


@require_GET
def edit(request: HttpRequest) -> HttpResponse:
    profile = _profile(request)
    show_first_visit_notice = not profile.first_visit_notice_seen
    if show_first_visit_notice:
        profile.first_visit_notice_seen = True
        profile.save(update_fields=["first_visit_notice_seen", "updated_at"])
    context = {
        **_preview_context(profile),
        "achievement_warnings": check_bullet_quality,
        "show_first_visit_notice": show_first_visit_notice,
    }
    return render(request, "resumes/edit.html", context)


@require_POST
def start_over(request: HttpRequest) -> HttpResponse:
    request.session.flush()
    return redirect("resumes:edit")


@require_POST
def undo(request: HttpRequest) -> HttpResponse:
    snapshot = request.session.pop("undo_snapshot", None)
    if snapshot:
        restore_profile_snapshot(_profile(request), snapshot)
        request.session.modified = True
    return redirect("resumes:edit")


@require_POST
def save_personal(request: HttpRequest) -> HttpResponse:
    profile = _profile(request)
    form = PersonalInfoForm(request.POST, instance=profile)
    if form.is_valid():
        capture_undo_snapshot(request, profile)
        form.save()
    return _render_with_preview(request, "resumes/partials/personal_form.html", {"personal_form": form})


@require_POST
def save_summary(request: HttpRequest) -> HttpResponse:
    profile = _profile(request)
    form = SummaryForm(request.POST, instance=profile)
    if form.is_valid():
        capture_undo_snapshot(request, profile)
        form.save()
    return _render_with_preview(request, "resumes/partials/summary_form.html", {"summary_form": form})


@require_POST
def save_theme(request: HttpRequest) -> HttpResponse:
    profile = _profile(request)
    form = ThemeForm(request.POST, instance=profile)
    if form.is_valid():
        capture_undo_snapshot(request, profile)
        form.save()
    return _render_with_preview(request, "resumes/partials/theme_form.html", {"theme_form": form})


@require_POST
def add_experience(request: HttpRequest) -> HttpResponse:
    profile = _profile(request)
    capture_undo_snapshot(request, profile)
    Experience.objects.create(profile=profile, order=next_order(profile.experiences.all()))
    return _render_list(request, "resumes/partials/experience_list.html")


@require_POST
def save_experience(request: HttpRequest, pk: int) -> HttpResponse:
    experience = get_object_or_404(Experience, pk=pk, profile=_profile(request))
    form = ExperienceForm(request.POST, instance=experience)
    if form.is_valid():
        capture_undo_snapshot(request, experience.profile)
        form.save()
    return _render_with_preview(
        request,
        "resumes/partials/experience_item.html",
        {"experience": experience, "experience_form": form},
    )


@require_http_methods(["DELETE", "POST"])
def delete_experience(request: HttpRequest, pk: int) -> HttpResponse:
    experience = get_object_or_404(Experience, pk=pk, profile=_profile(request))
    capture_undo_snapshot(request, experience.profile)
    experience.delete()
    return _render_list(request, "resumes/partials/experience_list.html")


@require_POST
def move_experience(request: HttpRequest, pk: int) -> HttpResponse:
    experience = get_object_or_404(Experience, pk=pk, profile=_profile(request))
    capture_undo_snapshot(request, experience.profile)
    move_ordered_item(experience, experience.profile.experiences.all(), request.POST.get("direction", ""))
    return _render_list(request, "resumes/partials/experience_list.html")


@require_POST
def add_achievement(request: HttpRequest, experience_id: int) -> HttpResponse:
    experience = get_object_or_404(Experience, pk=experience_id, profile=_profile(request))
    capture_undo_snapshot(request, experience.profile)
    Achievement.objects.create(experience=experience, order=next_order(experience.achievements.all()))
    return _render_with_preview(
        request,
        "resumes/partials/achievement_list.html",
        {"experience": experience},
    )


@require_POST
def save_achievement(request: HttpRequest, pk: int) -> HttpResponse:
    achievement = get_object_or_404(Achievement, pk=pk, experience__profile=_profile(request))
    form = AchievementForm(request.POST, instance=achievement)
    if form.is_valid():
        capture_undo_snapshot(request, achievement.experience.profile)
        form.save()
        verb = request.POST.get("replace_with")
        if verb:
            achievement.text = replace_weak_opener(achievement.text, verb)
            achievement.save(update_fields=["text", "updated_at"])
    achievement.refresh_from_db()
    return _render_with_preview(
        request,
        "resumes/partials/achievement_item.html",
        {
            "achievement": achievement,
            "achievement_form": AchievementForm(instance=achievement),
            "warnings": check_bullet_quality(achievement.text),
        },
    )


@require_http_methods(["DELETE", "POST"])
def delete_achievement(request: HttpRequest, pk: int) -> HttpResponse:
    achievement = get_object_or_404(Achievement, pk=pk, experience__profile=_profile(request))
    experience = achievement.experience
    capture_undo_snapshot(request, experience.profile)
    achievement.delete()
    return _render_with_preview(request, "resumes/partials/achievement_list.html", {"experience": experience})


@require_POST
def move_achievement(request: HttpRequest, pk: int) -> HttpResponse:
    achievement = get_object_or_404(Achievement, pk=pk, experience__profile=_profile(request))
    capture_undo_snapshot(request, achievement.experience.profile)
    move_ordered_item(achievement, achievement.experience.achievements.all(), request.POST.get("direction", ""))
    return _render_with_preview(
        request,
        "resumes/partials/achievement_list.html",
        {"experience": achievement.experience},
    )


def _list_view(
    request: HttpRequest,
    model: type[Education] | type[Skill] | type[Certification],
    template: str,
    factory: Callable[..., Any],
) -> HttpResponse:
    profile = _profile(request)
    capture_undo_snapshot(request, profile)
    factory(profile=profile, order=next_order(model.objects.filter(profile=profile)))
    return _render_list(request, template)


def _save_item(
    request: HttpRequest,
    pk: int,
    model: type[Education] | type[Skill] | type[Certification],
    form_class: type[EducationForm] | type[SkillForm] | type[CertificationForm],
    template: str,
    context_name: str,
) -> HttpResponse:
    item = get_object_or_404(model, pk=pk, profile=_profile(request))
    form = form_class(request.POST, instance=item)
    if form.is_valid():
        capture_undo_snapshot(request, item.profile)
        form.save()
    return _render_with_preview(request, template, {context_name: item, f"{context_name}_form": form})


def _delete_item(
    request: HttpRequest,
    pk: int,
    model: type[Education] | type[Skill] | type[Certification],
    template: str,
) -> HttpResponse:
    item = get_object_or_404(model, pk=pk, profile=_profile(request))
    capture_undo_snapshot(request, item.profile)
    item.delete()
    return _render_list(request, template)


def _move_item(
    request: HttpRequest,
    pk: int,
    model: type[Education] | type[Skill] | type[Certification],
    related_name: str,
    template: str,
) -> HttpResponse:
    item = get_object_or_404(model, pk=pk, profile=_profile(request))
    capture_undo_snapshot(request, item.profile)
    move_ordered_item(item, getattr(item.profile, related_name).all(), request.POST.get("direction", ""))
    return _render_list(request, template)


@require_POST
def add_education(request: HttpRequest) -> HttpResponse:
    return _list_view(request, Education, "resumes/partials/education_list.html", Education.objects.create)


@require_POST
def save_education(request: HttpRequest, pk: int) -> HttpResponse:
    return _save_item(request, pk, Education, EducationForm, "resumes/partials/education_item.html", "education_item")


@require_http_methods(["DELETE", "POST"])
def delete_education(request: HttpRequest, pk: int) -> HttpResponse:
    return _delete_item(request, pk, Education, "resumes/partials/education_list.html")


@require_POST
def move_education(request: HttpRequest, pk: int) -> HttpResponse:
    return _move_item(request, pk, Education, "education", "resumes/partials/education_list.html")


@require_POST
def add_skill(request: HttpRequest) -> HttpResponse:
    return _list_view(request, Skill, "resumes/partials/skill_list.html", Skill.objects.create)


@require_POST
def save_skill(request: HttpRequest, pk: int) -> HttpResponse:
    return _save_item(request, pk, Skill, SkillForm, "resumes/partials/skill_item.html", "skill")


@require_http_methods(["DELETE", "POST"])
def delete_skill(request: HttpRequest, pk: int) -> HttpResponse:
    return _delete_item(request, pk, Skill, "resumes/partials/skill_list.html")


@require_POST
def move_skill(request: HttpRequest, pk: int) -> HttpResponse:
    return _move_item(request, pk, Skill, "skills", "resumes/partials/skill_list.html")


@require_POST
def add_certification(request: HttpRequest) -> HttpResponse:
    return _list_view(
        request,
        Certification,
        "resumes/partials/certification_list.html",
        Certification.objects.create,
    )


@require_POST
def save_certification(request: HttpRequest, pk: int) -> HttpResponse:
    return _save_item(
        request,
        pk,
        Certification,
        CertificationForm,
        "resumes/partials/certification_item.html",
        "certification",
    )


@require_http_methods(["DELETE", "POST"])
def delete_certification(request: HttpRequest, pk: int) -> HttpResponse:
    return _delete_item(request, pk, Certification, "resumes/partials/certification_list.html")


@require_POST
def move_certification(request: HttpRequest, pk: int) -> HttpResponse:
    return _move_item(request, pk, Certification, "certifications", "resumes/partials/certification_list.html")


@ratelimit(key=_session_rate_key, rate="30/h", block=True)
@require_GET
def export_resume_view(request: HttpRequest, profile_id: int | None = None) -> HttpResponse:
    profile = _profile(request)
    if profile_id and profile_id != profile.id:
        return HttpResponseBadRequest("Profile does not belong to this session.")
    try:
        export_format = ExportFormat(request.GET.get("format", ExportFormat.PDF))
    except ValueError:
        return HttpResponseBadRequest("Unsupported export format.")
    theme = request.GET.get("theme", profile.chosen_theme)
    payload = export_resume(profile, theme, export_format)
    filename = f"resume.{export_format.value}"
    response = HttpResponse(payload, content_type=CONTENT_TYPES[export_format])
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@require_GET
def analyze(request: HttpRequest) -> HttpResponse:
    profile = _profile(request)
    return render(request, "resumes/analyze.html", {**_preview_context(profile), "analysis": None})


@ratelimit(key=_session_rate_key, rate="30/h", block=True)
@require_POST
def run_analyzer(request: HttpRequest) -> HttpResponse:
    profile = _profile(request)
    profile.jd_text = request.POST.get("jd_text", "")
    profile.save(update_fields=["jd_text", "updated_at"])
    analysis = analyze_job_description(profile, profile.jd_text)
    return render(
        request,
        "resumes/partials/analyzer_results.html",
        {"analysis": analysis, "profile": profile},
    )


@require_GET
def action_verbs(request: HttpRequest, achievement_id: int) -> HttpResponse:
    achievement = get_object_or_404(Achievement, pk=achievement_id, experience__profile=_profile(request))
    return render(
        request,
        "resumes/partials/action_verbs.html",
        {"achievement": achievement, "verbs": action_verb_suggestions(achievement.text)},
    )
