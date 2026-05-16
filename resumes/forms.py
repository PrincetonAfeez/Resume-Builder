"""Forms for the resumes app."""

from __future__ import annotations

from typing import Any

from django import forms

from .models import (
    AccentColor,
    Achievement,
    Certification,
    Education,
    Experience,
    FontPairing,
    Profile,
    Skill,
    Theme,
)


class AutosaveMixin:
    fields: dict[str, forms.Field]

    def _style_fields(self) -> None:
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (
                existing + " w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 "
                "shadow-sm outline-none focus:border-slate-900 focus:ring-2 focus:ring-slate-200"
            ).strip()


class PersonalInfoForm(AutosaveMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["full_name", "email", "phone", "location", "linkedin_url", "portfolio_url"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._style_fields()


class SummaryForm(AutosaveMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["professional_summary"]
        widgets = {"professional_summary": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._style_fields()


class ThemeForm(AutosaveMixin, forms.ModelForm):
    chosen_theme = forms.ChoiceField(choices=Theme.choices, widget=forms.RadioSelect)
    accent_color = forms.ChoiceField(choices=AccentColor.choices, widget=forms.RadioSelect)
    font_pairing = forms.ChoiceField(choices=FontPairing.choices)

    class Meta:
        model = Profile
        fields = ["chosen_theme", "accent_color", "font_pairing"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._style_fields()


class ExperienceForm(AutosaveMixin, forms.ModelForm):
    class Meta:
        model = Experience
        fields = ["company", "title", "location", "start_date", "end_date", "current_role"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._style_fields()

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean() or {}
        start_date = cleaned.get("start_date")
        end_date = cleaned.get("end_date")
        current_role = cleaned.get("current_role")
        if current_role and end_date:
            self.add_error("end_date", "Leave end date empty for a current role.")
        if start_date and end_date and end_date < start_date:
            self.add_error("end_date", "End date must be after start date.")
        return cleaned


class AchievementForm(AutosaveMixin, forms.ModelForm):
    class Meta:
        model = Achievement
        fields = ["text"]
        widgets = {"text": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._style_fields()


class EducationForm(AutosaveMixin, forms.ModelForm):
    class Meta:
        model = Education
        fields = ["institution", "degree", "field", "start_date", "end_date", "gpa", "notes"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._style_fields()

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean() or {}
        start_date = cleaned.get("start_date")
        end_date = cleaned.get("end_date")
        if start_date and end_date and end_date < start_date:
            self.add_error("end_date", "End date must be after start date.")
        return cleaned


class SkillForm(AutosaveMixin, forms.ModelForm):
    proficiency = forms.TypedChoiceField(
        coerce=int,
        choices=[(value, "*" * value) for value in range(1, 6)],
        widget=forms.RadioSelect,
    )

    class Meta:
        model = Skill
        fields = ["name", "category", "proficiency"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._style_fields()


class CertificationForm(AutosaveMixin, forms.ModelForm):
    class Meta:
        model = Certification
        fields = ["name", "issuing_body", "date_earned", "expiry", "credential_id"]
        widgets = {
            "date_earned": forms.DateInput(attrs={"type": "date"}),
            "expiry": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._style_fields()

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean() or {}
        date_earned = cleaned.get("date_earned")
        expiry = cleaned.get("expiry")
        if date_earned and expiry and expiry < date_earned:
            self.add_error("expiry", "Expiry must be on or after date earned.")
        return cleaned
