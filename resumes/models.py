"""Models for the resumes app."""

from __future__ import annotations

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Theme(models.TextChoices):
    CLASSIC = "classic", "Classic"
    MODERN = "modern", "Modern"
    MINIMAL = "minimal", "Minimal"


class AccentColor(models.TextChoices):
    SLATE = "slate", "Slate"
    BLUE = "blue", "Blue"
    EMERALD = "emerald", "Emerald"
    ROSE = "rose", "Rose"
    AMBER = "amber", "Amber"
    VIOLET = "violet", "Violet"
    CYAN = "cyan", "Cyan"
    STONE = "stone", "Stone"


class FontPairing(models.TextChoices):
    SERIF = "serif", "Serif"
    SANS = "sans", "Sans"
    EDITORIAL = "editorial", "Editorial"
    COMPACT = "compact", "Compact"


class SkillCategory(models.TextChoices):
    TECHNICAL = "technical", "Technical"
    LANGUAGE = "language", "Language"
    SOFT = "soft", "Soft"


class Profile(models.Model):
    session_key = models.CharField(max_length=64, unique=True)
    full_name = models.CharField(max_length=140, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    location = models.CharField(max_length=120, blank=True)
    linkedin_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    professional_summary = models.TextField(blank=True)
    chosen_theme = models.CharField(
        max_length=20,
        choices=Theme.choices,
        default=Theme.CLASSIC,
    )
    accent_color = models.CharField(
        max_length=20,
        choices=AccentColor.choices,
        default=AccentColor.BLUE,
    )
    font_pairing = models.CharField(
        max_length=20,
        choices=FontPairing.choices,
        default=FontPairing.SANS,
    )
    jd_text = models.TextField(blank=True)
    first_visit_notice_seen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self) -> str:
        return self.full_name or f"Session {self.session_key[:8]}"

    def contact_complete(self) -> bool:
        return bool(self.full_name and self.email and self.phone and self.location)


class OrderedProfileModel(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["order", "id"]


class Experience(OrderedProfileModel):
    profile = models.ForeignKey(
        Profile,
        related_name="experiences",
        on_delete=models.CASCADE,
    )
    company = models.CharField(max_length=160, blank=True)
    title = models.CharField(max_length=160, blank=True)
    location = models.CharField(max_length=120, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    current_role = models.BooleanField(default=False)

    class Meta(OrderedProfileModel.Meta):
        verbose_name = "experience"
        verbose_name_plural = "experience"

    def __str__(self) -> str:
        return f"{self.title or 'Role'} at {self.company or 'Company'}"

    def date_range(self) -> str:
        start = self.start_date.strftime("%b %Y") if self.start_date else ""
        end = "Present" if self.current_role else self.end_date.strftime("%b %Y") if self.end_date else ""
        if start and end:
            return f"{start} - {end}"
        return start or end


class Achievement(models.Model):
    experience = models.ForeignKey(
        Experience,
        related_name="achievements",
        on_delete=models.CASCADE,
    )
    order = models.PositiveIntegerField(default=0)
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.text[:80] or "Achievement"


class Education(OrderedProfileModel):
    profile = models.ForeignKey(
        Profile,
        related_name="education",
        on_delete=models.CASCADE,
    )
    institution = models.CharField(max_length=160, blank=True)
    degree = models.CharField(max_length=160, blank=True)
    field = models.CharField(max_length=160, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    gpa = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)

    class Meta(OrderedProfileModel.Meta):
        verbose_name = "education"
        verbose_name_plural = "education"

    def __str__(self) -> str:
        return self.institution or "Education"

    def date_range(self) -> str:
        start = self.start_date.strftime("%b %Y") if self.start_date else ""
        end = self.end_date.strftime("%b %Y") if self.end_date else ""
        if start and end:
            return f"{start} - {end}"
        return start or end


class Skill(OrderedProfileModel):
    profile = models.ForeignKey(
        Profile,
        related_name="skills",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=120, blank=True)
    category = models.CharField(
        max_length=20,
        choices=SkillCategory.choices,
        default=SkillCategory.TECHNICAL,
    )
    proficiency = models.PositiveSmallIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )

    def __str__(self) -> str:
        return self.name or "Skill"


class Certification(OrderedProfileModel):
    profile = models.ForeignKey(
        Profile,
        related_name="certifications",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=160, blank=True)
    issuing_body = models.CharField(max_length=160, blank=True)
    date_earned = models.DateField(null=True, blank=True)
    expiry = models.DateField(null=True, blank=True)
    credential_id = models.CharField(max_length=120, blank=True)

    def __str__(self) -> str:
        return self.name or "Certification"
