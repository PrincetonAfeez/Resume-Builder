"""Admin for the resumes app."""

from __future__ import annotations

from django.contrib import admin

from .models import Achievement, Certification, Education, Experience, Profile, Skill


class AchievementInline(admin.TabularInline):
    model = Achievement
    extra = 0


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    inlines = [AchievementInline]
    list_display = ["title", "company", "profile", "order", "current_role"]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["__str__", "session_key", "chosen_theme", "updated_at"]
    search_fields = ["full_name", "email", "session_key"]


admin.site.register(Education)
admin.site.register(Skill)
admin.site.register(Certification)
