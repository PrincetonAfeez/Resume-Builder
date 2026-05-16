"""URLs for the resumes app."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "resumes"

urlpatterns = [
    path("resume/edit/", views.edit, name="edit"),
    path("resume/start-over/", views.start_over, name="start_over"),
    path("resume/undo/", views.undo, name="undo"),
    path("resume/personal/save/", views.save_personal, name="save_personal"),
    path("resume/summary/save/", views.save_summary, name="save_summary"),
    path("resume/theme/save/", views.save_theme, name="save_theme"),
    path("resume/experience/add/", views.add_experience, name="add_experience"),
    path("resume/experience/<int:pk>/save/", views.save_experience, name="save_experience"),
    path("resume/experience/<int:pk>/delete/", views.delete_experience, name="delete_experience"),
    path("resume/experience/<int:pk>/move/", views.move_experience, name="move_experience"),
    path("resume/experience/<int:experience_id>/achievement/add/", views.add_achievement, name="add_achievement"),
    path("resume/achievement/<int:pk>/save/", views.save_achievement, name="save_achievement"),
    path("resume/achievement/<int:pk>/delete/", views.delete_achievement, name="delete_achievement"),
    path("resume/achievement/<int:pk>/move/", views.move_achievement, name="move_achievement"),
    path("resume/education/add/", views.add_education, name="add_education"),
    path("resume/education/<int:pk>/save/", views.save_education, name="save_education"),
    path("resume/education/<int:pk>/delete/", views.delete_education, name="delete_education"),
    path("resume/education/<int:pk>/move/", views.move_education, name="move_education"),
    path("resume/skill/add/", views.add_skill, name="add_skill"),
    path("resume/skill/<int:pk>/save/", views.save_skill, name="save_skill"),
    path("resume/skill/<int:pk>/delete/", views.delete_skill, name="delete_skill"),
    path("resume/skill/<int:pk>/move/", views.move_skill, name="move_skill"),
    path("resume/certification/add/", views.add_certification, name="add_certification"),
    path("resume/certification/<int:pk>/save/", views.save_certification, name="save_certification"),
    path("resume/certification/<int:pk>/delete/", views.delete_certification, name="delete_certification"),
    path("resume/certification/<int:pk>/move/", views.move_certification, name="move_certification"),
    path("resume/export/", views.export_resume_view, name="export"),
    path("resume/<int:profile_id>/export/", views.export_resume_view, name="export_with_id"),
    path("resume/analyze/", views.analyze, name="analyze"),
    path("resume/analyze/run/", views.run_analyzer, name="run_analyzer"),
    path("resume/action-verbs/<int:achievement_id>/", views.action_verbs, name="action_verbs"),
]
