"""Analysis services for the resumes app."""

from __future__ import annotations

import re
from dataclasses import dataclass

from resumes.models import Profile

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "our",
    "that",
    "the",
    "their",
    "this",
    "to",
    "with",
    "you",
    "your",
}

WEAK_OPENERS = (
    "responsible for",
    "helped with",
    "worked on",
    "duties included",
    "assisted in",
)

ACTION_VERBS = {
    "Execution": ["Delivered", "Launched", "Built", "Automated", "Implemented"],
    "Leadership": ["Directed", "Guided", "Orchestrated", "Mentored", "Mobilized"],
    "Analysis": ["Analyzed", "Diagnosed", "Forecasted", "Modeled", "Synthesized"],
    "Communication": ["Presented", "Translated", "Documented", "Negotiated", "Briefed"],
    "Operations": ["Streamlined", "Coordinated", "Standardized", "Optimized", "Scaled"],
}


@dataclass(frozen=True)
class BulletWarning:
    code: str
    message: str


@dataclass(frozen=True)
class CompletenessResult:
    score: int
    breakdown: list[tuple[str, int, bool]]


@dataclass(frozen=True)
class KeywordAnalysis:
    present: list[str]
    missing: list[str]
    match_percentage: int


def check_bullet_quality(text: str) -> list[BulletWarning]:
    stripped = text.strip()
    lower = stripped.lower()
    warnings: list[BulletWarning] = []

    if any(lower.startswith(opener) for opener in WEAK_OPENERS):
        warnings.append(BulletWarning("weak_opener", "Starts with a weak opener."))
    if stripped and not re.search(r"(\d|%|\$)", stripped):
        warnings.append(BulletWarning("no_quantification", "No visible quantification."))
    if len(stripped) > 180:
        warnings.append(BulletWarning("too_long", "Longer than two lines."))
    if re.search(r"\b(was|were|been|being)\s+\w+ed\b", lower):
        warnings.append(BulletWarning("passive_voice", "May use passive voice."))

    return warnings


def action_verb_suggestions(text: str) -> list[str]:
    lower = text.strip().lower()
    if not any(lower.startswith(opener) for opener in WEAK_OPENERS):
        return []
    return [verb for group in ACTION_VERBS.values() for verb in group][:5]


def replace_weak_opener(text: str, verb: str) -> str:
    stripped = text.strip()
    for opener in WEAK_OPENERS:
        if stripped.lower().startswith(opener):
            remainder = stripped[len(opener) :].lstrip(" ,:-")
            return f"{verb} {remainder}".strip()
    return f"{verb} {stripped}".strip()


def completeness_score(profile: Profile) -> CompletenessResult:
    experiences = list(profile.experiences.prefetch_related("achievements").all())
    education = list(profile.education.all())
    skills = list(profile.skills.all())
    bullets = [achievement for experience in experiences for achievement in experience.achievements.all()]

    checks = [
        ("Has summary", 10, bool(profile.professional_summary.strip())),
        ("Summary has substance", 10, len(profile.professional_summary.strip()) > 50),
        ("Has experience", 15, bool(experiences)),
        (
            "Every experience has two bullets",
            15,
            bool(experiences) and all(len(experience.achievements.all()) >= 2 for experience in experiences),
        ),
        (
            "Every experience has dates",
            10,
            bool(experiences)
            and all(
                experience.start_date and (experience.current_role or experience.end_date)
                for experience in experiences
            ),
        ),
        ("Has education", 10, bool(education)),
        ("Has three skills", 10, len(skills) >= 3),
        ("Contact info complete", 10, profile.contact_complete()),
        ("No flagged bullets", 10, all(not check_bullet_quality(bullet.text) for bullet in bullets)),
    ]
    return CompletenessResult(sum(points for _label, points, passed in checks if passed), checks)


def analyze_job_description(profile: Profile, jd_text: str, top_n: int = 20) -> KeywordAnalysis:
    keywords = extract_keywords(jd_text, top_n=top_n)
    resume_text = profile_resume_text(profile).lower()
    present = [keyword for keyword in keywords if keyword.lower() in resume_text]
    missing = [keyword for keyword in keywords if keyword not in present]
    match = round((len(present) / len(keywords)) * 100) if keywords else 0
    return KeywordAnalysis(present=present, missing=missing, match_percentage=match)


def extract_keywords(text: str, top_n: int = 20) -> list[str]:
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
    except Exception:
        return _fallback_keywords(text, top_n)

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words=list(STOPWORDS),
        ngram_range=(1, 2),
        max_features=top_n,
    )
    try:
        matrix = vectorizer.fit_transform([text])
    except ValueError:
        return []
    scores = matrix.toarray()[0]
    terms = vectorizer.get_feature_names_out()
    ranked = sorted(zip(terms, scores, strict=True), key=lambda item: item[1], reverse=True)
    return [term for term, score in ranked if score > 0][:top_n]


def profile_resume_text(profile: Profile) -> str:
    parts = [
        profile.full_name,
        profile.email,
        profile.phone,
        profile.location,
        profile.professional_summary,
    ]
    for experience in profile.experiences.prefetch_related("achievements").all():
        parts.extend([experience.company, experience.title, experience.location])
        parts.extend(achievement.text for achievement in experience.achievements.all())
    for item in profile.education.all():
        parts.extend([item.institution, item.degree, item.field, item.notes])
    parts.extend(skill.name for skill in profile.skills.all())
    for certification in profile.certifications.all():
        parts.extend([certification.name, certification.issuing_body, certification.credential_id])
    return " ".join(part for part in parts if part)


def _fallback_keywords(text: str, top_n: int) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9+#.-]{2,}", text.lower())
    counts: dict[str, int] = {}
    for word in words:
        if word not in STOPWORDS:
            counts[word] = counts.get(word, 0) + 1
    return [word for word, _count in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:top_n]]
