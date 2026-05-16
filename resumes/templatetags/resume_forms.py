"""Resume forms template tags for the resumes app."""

from __future__ import annotations

from django import template

from resumes.forms import AchievementForm, CertificationForm, EducationForm, ExperienceForm, SkillForm
from resumes.models import Achievement, Certification, Education, Experience, Skill
from resumes.services.analysis import check_bullet_quality

register = template.Library()


@register.filter
def experience_form(experience: Experience) -> ExperienceForm:
    return ExperienceForm(instance=experience)


@register.filter
def achievement_form(achievement: Achievement) -> AchievementForm:
    return AchievementForm(instance=achievement)


@register.filter
def education_form(education: Education) -> EducationForm:
    return EducationForm(instance=education)


@register.filter
def skill_form(skill: Skill) -> SkillForm:
    return SkillForm(instance=skill)


@register.filter
def certification_form(certification: Certification) -> CertificationForm:
    return CertificationForm(instance=certification)


@register.filter
def bullet_warnings(text: str):
    return check_bullet_quality(text)


@register.filter
def stars(value: int) -> str:
    value = int(value or 0)
    return "*" * value + "-" * (5 - value)
