"""Demo resume data for screenshots and browser tests."""

from __future__ import annotations

from resumes.models import Achievement, Education, Experience, Profile, Skill


def seed_demo_profile(session_key: str) -> Profile:
    profile, _created = Profile.objects.get_or_create(
        session_key=session_key,
        defaults={
            "full_name": "Ada Lovelace",
            "email": "ada@example.com",
            "phone": "555-0100",
            "location": "London, UK",
            "linkedin_url": "https://linkedin.com/in/ada",
            "portfolio_url": "https://ada.example.com",
            "professional_summary": (
                "Analytical software leader with deep experience building reliable systems "
                "and translating complex ideas into practical tools."
            ),
            "chosen_theme": "classic",
            "first_visit_notice_seen": True,
        },
    )
    if profile.experiences.exists():
        return profile

    experience = Experience.objects.create(
        profile=profile,
        company="Analytical Engines",
        title="Principal Engineer",
        location="Remote",
        start_date="2022-01-01",
        current_role=True,
        order=1,
    )
    Achievement.objects.create(
        experience=experience,
        text="Built 3 automated reporting workflows that reduced manual review time by 40%.",
        order=1,
    )
    Achievement.objects.create(
        experience=experience,
        text="Implemented reliability dashboards used by 12 cross-functional teams.",
        order=2,
    )
    Education.objects.create(
        profile=profile,
        institution="University of London",
        degree="BS",
        field="Mathematics",
        order=1,
    )
    Skill.objects.create(profile=profile, name="Python", category="technical", proficiency=5, order=1)
    Skill.objects.create(profile=profile, name="Django", category="technical", proficiency=5, order=2)
    Skill.objects.create(profile=profile, name="Communication", category="soft", proficiency=4, order=3)
    return profile
