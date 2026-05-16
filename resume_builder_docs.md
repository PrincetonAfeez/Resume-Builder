# Architecture Decision Record
## App — Resume Builder
**Career Tools Group | Document 1 of 5**
**Status: Accepted**

---

## Context

Resume Builder is a session-only browser app for creating one polished resume and keeping it by downloading PDF, DOCX, or TXT. The application intentionally avoids accounts, passwords, and saved resume libraries. A Django session cookie identifies the working profile, and the durable persistence step is export.

The project is larger than a simple form app. It includes HTMX autosave, a split-screen editor, live preview, three themes, accent colors, font pairings, ordered resume sections, undo, start-over, PDF/DOCX/TXT export, job-description keyword analysis, bullet-quality warnings, action verb suggestions, completeness scoring, export/analyzer rate limits, stale-profile pruning, vendored frontend assets (no production CDN dependency), Railway deployment, a health endpoint, and release-time checks for WeasyPrint.

The decision was to build Resume Builder as a Django monolith with server-rendered templates and HTMX partials, while keeping business rules in focused services.

---

## Decisions

### Decision 1 — Session-only identity over accounts

**Chosen:** A `Profile` is keyed by `request.session.session_key`. The browser session is the identity.

**Rejected:** User accounts, passwords, login/logout, saved resume libraries, and multi-resume dashboards.

**Reason:** V1 is optimized for quickly building and exporting one resume. Account functionality would add authentication, password reset, account deletion, authorization, privacy policy scope, and persistent storage obligations. The app is intentionally honest: if the user wants to keep the resume, they download it.

---

### Decision 2 — Django + HTMX over a JavaScript SPA

**Chosen:** Django renders full pages and HTMX partials. The server owns forms, validation, CSRF, persistence, preview context, and export behavior.

**Rejected:** React/Next.js, a separate API, or client-side state as the source of truth.

**Reason:** The app is form-heavy and server-owned. Django provides the ORM, forms, sessions, templates, middleware, management commands, and deployment conventions. HTMX provides autosave and partial swaps without creating a second frontend architecture.

---

### Decision 3 — Normalized resume models over a single JSON blob

**Chosen:** Store resume content in normalized models: `Profile`, `Experience`, `Achievement`, `Education`, `Skill`, and `Certification`.

**Rejected:** One JSON field containing all resume data.

**Reason:** Resume sections need validation, ordering, child relationships, partial updates, and exports. Normalized rows make add/save/delete/move operations deterministic and testable. They also allow Django's related managers to support preview and export generation cleanly.

---

### Decision 4 — Explicit ordered rows

**Chosen:** Ordered resume sections use an `order` field and sort by `order`, then `id`. Movement swaps adjacent order values.

**Rejected:** Ordering by creation timestamp or list position in client-side state.

**Reason:** Resume section order matters. Explicit ordering makes reordering stable across database reads and easy to test. The shared `move_ordered_item()` service keeps this logic out of templates and individual views.

---

### Decision 5 — Thin views and service modules

**Chosen:** Views handle HTTP concerns and delegate business behavior to service modules:

- `resumes.services.profile`
- `resumes.services.resume_export`
- `resumes.services.analysis`

**Rejected:** Putting export, analysis, undo, pruning, and scoring logic directly in views.

**Reason:** The app has many workflows. Service modules make the most important logic testable outside request handling and prevent the view file from becoming the only place where product rules live.

---

### Decision 6 — HTMX autosave with partial templates

**Chosen:** Each section posts to a small endpoint and receives a partial response. The response includes preview context. Valid saves set `HX-Trigger: resume:saved`; invalid saves set `HX-Trigger: resume:invalid` so the UI can show a save indicator without implying success.

**Rejected:** A single full-page submit button or client-side state management.

**Reason:** Resume editing benefits from immediate feedback. HTMX gives autosave and live preview while keeping Django forms and validation authoritative.

---

### Decision 7 — One-step undo through session snapshots

**Chosen:** Before mutations, the app reloads the profile from the database, serializes it and related rows into `request.session["undo_snapshot"]`, then applies the change. Undo restores that snapshot transactionally.

**Rejected:** Full version history, per-field undo, or an audit-log table.

**Reason:** The app needs a practical recovery mechanism, not a full revision system. A one-level undo fits the V1 scope and the session-only model.

---

### Decision 8 — Export is the persistence boundary

**Chosen:** The app supports PDF, DOCX, and TXT exports. PDF uses WeasyPrint when available (themed HTML with a resolved `file://` stylesheet URI) and a minimal fallback PDF when native libraries are unavailable locally. DOCX uses `python-docx`. TXT is ATS-friendly plain text.

**Rejected:** Server-side saved resume libraries or cloud document storage.

**Reason:** Download is the intended durability step. This keeps storage and privacy simple while still giving users useful output formats.

---

### Decision 9 — Visual theme applies to preview/PDF, not full DOCX theming

**Chosen:** Theme choices affect browser preview and PDF export. DOCX is structured and editable rather than theme-perfect.

**Rejected:** Attempting exact DOCX visual parity with PDF themes.

**Reason:** DOCX fidelity is harder and less valuable than clean structure. PDF is the polished format; DOCX is the editable format.

---

### Decision 10 — Deterministic JD analyzer over LLM features

**Chosen:** Use keyword extraction, present/missing keyword groups, and a match percentage. Keywords are matched with token boundaries (not naive substring search). TF-IDF is attempted through scikit-learn, with a fallback keyword counter.

**Rejected:** LLM-powered rewriting or job-tailoring features in V1.

**Reason:** Deterministic analysis is cheaper, safer, testable, and privacy-friendly. Token matching avoids false positives (for example `go` inside `django`). LLM features would add scope, privacy, prompt, and reliability questions.

---

### Decision 11 — Rate-limited heavy operations

**Chosen:** Exports and analyzer runs are rate-limited at 30/hour per session.

**Rejected:** No throttling.

**Reason:** PDF rendering and analysis are heavier than ordinary autosave requests. Session-based throttling matches the identity model and provides basic abuse protection.

---

### Decision 12 — Stale profile pruning

**Chosen:** A management command deletes profiles whose backing sessions have expired.

**Rejected:** Keeping session-created profiles forever.

**Reason:** The app is session-only. Expired sessions should not leave old profiles in the database indefinitely. A separate Railway service can run the pruning command on a schedule.

---

### Decision 13 — Production runtime checks for WeasyPrint

**Chosen:** `check_production_runtime` runs on Railway release (after `collectstatic` and migrations). It logs `production_runtime weasyprint=available` and succeeds, or logs `production_runtime weasyprint=unavailable` and fails the release with `CommandError`. Railway/Nixpacks installs the needed native packages. Local dev may still use a minimal fallback PDF when WeasyPrint is missing.

**Rejected:** Assuming PDF runtime support will work silently, or treating missing WeasyPrint on release as a successful deploy.

**Reason:** WeasyPrint depends on native libraries. Failing release when PDF rendering is unavailable prevents shipping production without themed PDF export.

---

### Decision 14 — Vendored frontend assets over public CDNs

**Chosen:** Serve Tailwind CSS, HTMX, and Lucide from `resumes/static/resumes/vendor/` via Django static files and WhiteNoise. Pin versions and rebuild Tailwind from `frontend/input.css` when template classes change. See `docs/adr/0010-vendored-frontend-assets.md`.

**Rejected:** Loading Tailwind, HTMX, and Lucide from public CDNs in production templates.

**Reason:** Editor styling and autosave must not depend on third-party CDN availability, latency, or policy changes. `collectstatic` ships vendor assets with the app.

---

## Consequences

**Positive:**
- The app stays scoped to one resume and one session.
- No account system reduces privacy and security burden.
- Normalized models support ordered editing and clean exports.
- HTMX gives modern autosave without a frontend framework.
- Export formats cover polished, editable, and ATS-friendly needs.
- Undo, bullet warnings, completeness scoring, and analyzer results provide practical feedback.
- Rate limits and pruning reflect operational maturity.
- WeasyPrint runtime checks surface deployment issues early.
- Vendored frontend assets keep the editor usable without CDN dependency.

**Negative / Trade-offs:**
- Session loss means resume loss unless the user exports.
- No multi-resume library exists in V1.
- DOCX is not theme-perfect.
- WeasyPrint introduces native runtime dependency risk.
- Vendored CSS/JS requires rebuild scripts when UI classes or pinned versions change.
- HTMX partials create many endpoints and templates.
- One-level undo is useful but limited.
- Local SQLite differs from production PostgreSQL.

---

## Alternatives Not Explored

- Account-based SaaS model.
- Multiple resumes per user.
- Persistent resume libraries.
- LLM-powered rewrites.
- Full DOCX theme fidelity.
- Client-side resume builder with local storage.
- Background PDF queue.

---

*Constitution reference: Article 1 (Python fundamentals and architectural thinking), Article 3.4 (larger project classification), Article 4 (engineering quality), Article 6 (behavior verification), and Article 7 (progressive complexity).*

---


# Technical Design Document
## App — Resume Builder
**Career Tools Group | Document 2 of 5**

---

## Overview

Resume Builder is a Django application for creating one resume in a browser session. It includes a split-screen editor, HTMX autosave, live preview, resume themes, ordered sections, undo, PDF/DOCX/TXT export, job-description analysis, bullet-quality feedback, rate limits, stale-profile pruning, and production runtime checks.

**Django project:** `resume_builder`  
**Primary app:** `resumes`  
**Local settings:** `resume_builder.settings.dev`  
**Production settings:** `resume_builder.settings.prod`  
**Runtime target:** Python 3.14  
**Local database:** SQLite  
**Production database:** PostgreSQL through `DATABASE_URL`  
**UI model:** Django templates + HTMX partials

---

## Data Flow

### First visit

```text
GET /resume/edit/
  -> SessionMiddleware
  -> ProfileSessionMiddleware
  -> get_or_create_profile(request)
  -> request.resume_profile
  -> edit view
  -> build_resume_context + completeness_score + forms
  -> render resumes/edit.html
```

### Autosave

```text
HTMX POST section save endpoint
  -> bind ModelForm
  -> if valid: capture_undo_snapshot + save
  -> rebuild preview context
  -> render section partial
  -> HX-Trigger: resume:saved (valid) or resume:invalid (errors)
```

### Export

```text
GET /resume/export/?format=pdf|docx|txt
  -> rate limit by session
  -> build_resume_context(profile, theme)
  -> export_pdf/export_docx/export_txt
  -> attachment response
```

### Analyzer

```text
POST /resume/analyze/run/
  -> rate limit by session
  -> save jd_text
  -> extract_keywords(jd_text)
  -> token-match keywords against profile_resume_text(profile)
  -> render analyzer_results partial
```

### Undo

```text
Before mutation: serialize profile graph into session
POST /resume/undo/
  -> pop undo_snapshot
  -> transactionally restore profile and related rows
  -> redirect to editor
```

---

## Module-Level Structure

```text
Resume-Builder/
  manage.py
  resume_builder/
    settings/base.py
    settings/dev.py
    settings/prod.py
    urls.py
    wsgi.py
    asgi.py
  resumes/
    models.py
    forms.py
    middleware.py
    urls.py
    views.py
    services/
      profile.py
      resume_export.py
      analysis.py
    management/commands/
      prune_stale_profiles.py
      check_production_runtime.py
  templates/
  static/
  frontend/input.css
  resumes/static/resumes/vendor/
  scripts/vendor_frontend_assets.py
  tests/
  docs/adr/
  docs/screenshots/
  scripts/generate_readme_screenshots.py
  requirements.txt
  requirements-dev.txt
  pyproject.toml
  railway.toml
  railway.prune.toml
  nixpacks.toml
  Procfile
```

---

## Module Dependency Graph

```text
resume_builder.urls
  -> admin
  -> health JsonResponse
  -> redirect home to resumes:edit
  -> include resumes.urls

resumes.middleware
  -> services.profile.get_or_create_profile

resumes.views
  -> forms
  -> models
  -> services.profile
  -> services.resume_export
  -> services.analysis
  -> django-ratelimit

services.profile
  -> Django Session model
  -> transaction.atomic
  -> Profile/Experience/Achievement/Education/Skill/Certification

services.resume_export
  -> render_to_string
  -> WeasyPrint
  -> python-docx
  -> fallback PDF generator

services.analysis
  -> regex
  -> dataclasses
  -> scikit-learn TF-IDF optional path
  -> fallback keyword extraction

management commands
  -> prune_stale_profiles
  -> weasyprint_runtime_available
```

---

## Core Data Structures

### `Profile`

One resume profile tied to a browser session.

Important fields:
- `session_key`
- `full_name`
- `email`
- `phone`
- `location`
- `linkedin_url`
- `portfolio_url`
- `professional_summary`
- `chosen_theme`
- `accent_color`
- `font_pairing`
- `jd_text`
- `first_visit_notice_seen`
- timestamps

Important method:

```python
contact_complete()
```

---

### `Experience`

Ordered work experience row with company, title, location, start/end dates, and `current_role`.

Important method:

```python
date_range()
```

---

### `Achievement`

Ordered bullet attached to an experience.

---

### `Education`

Ordered education row with institution, degree, field, date range, GPA, and notes.

---

### `Skill`

Ordered skill row with category and proficiency from 1 to 5.

---

### `Certification`

Ordered certification row with issuing body, dates, and credential ID.

---

### Choice enums

`Theme`:
- classic
- modern
- minimal

`AccentColor`:
- slate
- blue
- emerald
- rose
- amber
- violet
- cyan
- stone

`FontPairing`:
- serif
- sans
- editorial
- compact

`SkillCategory`:
- technical
- language
- soft

---

### Analysis dataclasses

```python
BulletWarning(code, message)
CompletenessResult(score, breakdown)
KeywordAnalysis(present, missing, match_percentage)
```

---

## Function and Class Reference

### `ProfileSessionMiddleware`

Ensures normal resume requests have `request.resume_profile`. Skips admin, static, health, and favicon paths.

---

### `get_or_create_profile(request)`

Creates a session if needed, then gets or creates a `Profile` for that session key.

---

### `next_order(queryset)`

Returns one greater than the current max `order` value. Add-item views call it inside `transaction.atomic()` with `select_for_update()` on the sibling queryset to avoid duplicate order values under concurrent posts.

---

### `move_ordered_item(item, siblings, direction)`

Moves an ordered item up or down by swapping `order` values with an adjacent sibling. Invalid direction and boundary moves are no-ops.

---

### `capture_undo_snapshot(request, profile)`

Reloads the profile from the database, serializes it and related rows, and stores the snapshot in the session.

---

### `restore_profile_snapshot(profile, snapshot)`

Restores profile fields and recreates related rows inside `transaction.atomic()`.

---

### `prune_stale_profiles()`

Deletes profiles whose session keys are not present in active Django sessions.

---

### `build_resume_context(profile, theme=None)`

Prefetches the resume graph and returns profile, theme, template name, experiences, education, skills, and certifications.

---

### `export_resume(profile, theme, format)`

Dispatches to PDF, DOCX, or TXT export.

---

### `export_pdf(context)`

Renders themed PDF through WeasyPrint using `resolve_pdf_stylesheet_uri()` and `BASE_DIR` as `base_url`. If native runtime is missing locally, returns a minimal fallback PDF (production release fails `check_production_runtime` instead).

---

### `export_docx(context)`

Builds structured DOCX using `python-docx`.

---

### `export_txt(context)`

Builds ATS-friendly plain text.

---

### `weasyprint_runtime_available()`

Tests whether WeasyPrint can produce a small PDF in the current runtime.

---

### `check_bullet_quality(text)`

Flags weak opener, missing quantification, excessive length, and possible passive voice.

---

### `completeness_score(profile)`

Scores summary, experience, bullets, dates, education, skills, contact info, and bullet quality.

---

### `analyze_job_description(profile, jd_text)`

Extracts keywords, token-matches them to resume text, and returns present/missing keywords plus match percentage.

---

## View Reference

Primary views include:
- `edit`
- `start_over`
- `undo`
- `save_personal`
- `save_summary`
- `save_theme`
- add/save/delete/move views for experiences, achievements, education, skills, and certifications
- `export_resume_view`
- `analyze`
- `run_analyzer`
- `action_verbs`

The views use `get_object_or_404()` with profile ownership filters for object-level operations.

---

## Error Handling Strategy

- Invalid forms re-render partials with errors.
- Foreign profile export returns HTTP 400.
- Unsupported export format returns HTTP 400.
- Rate-limited export/analyzer calls return 403.
- Missing or foreign objects return 404.
- WeasyPrint `OSError` falls back to minimal PDF.
- Invalid movement direction no-ops.
- Stale pruning logs and prints deletion counts.

---

## External Dependencies

Runtime:
- Django
- django-environ
- gunicorn
- whitenoise
- psycopg
- python-docx
- weasyprint
- scikit-learn
- django-ratelimit
- sentry-sdk

Development/CI:
- black
- isort
- ruff
- django-stubs
- mypy
- pytest
- pytest-cov
- pytest-django
- playwright

---

## Concurrency Model

The web app is synchronous Django served by Gunicorn. The pruning workflow is not a background worker inside the web process; it is a separate Railway service or command that runs and exits.

---

## Known Limitations

- No accounts.
- No multiple resumes.
- No resume duplication.
- No share links.
- No cover letters.
- No job tracker.
- No LinkedIn import.
- No analytics.
- No collaboration.
- No LLM-powered features.
- DOCX is structured, not theme-perfect.
- Session loss loses resume data unless exported.
- WeasyPrint full PDF quality depends on native runtime libraries.

---

## Verification Summary

Tests cover models, forms, services, views, exports, analyzer, rate limits, pruning, undo snapshots, first-visit notice, object ownership, WeasyPrint/E2E paths, and README screenshots.

---

*Constitution reference: Article 4 (engineering quality), Article 6 (behavior verification), Article 7 (progressive complexity), and Article 8 (valid learner work).*

---


# Interface Design Specification
## App — Resume Builder
**Career Tools Group | Document 3 of 5**

---

## Public Web Interface

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Redirect to editor |
| GET | `/health/` | JSON health check |
| GET | `/resume/edit/` | Resume editor |
| POST | `/resume/start-over/` | Flush session and restart |
| POST | `/resume/undo/` | Restore one undo snapshot |
| POST | `/resume/personal/save/` | Save personal info |
| POST | `/resume/summary/save/` | Save summary |
| POST | `/resume/theme/save/` | Save theme/accent/font |
| POST | `/resume/experience/add/` | Add experience |
| POST | `/resume/experience/<pk>/save/` | Save experience |
| POST/DELETE | `/resume/experience/<pk>/delete/` | Delete experience |
| POST | `/resume/experience/<pk>/move/` | Move experience |
| POST | `/resume/experience/<experience_id>/achievement/add/` | Add bullet |
| POST | `/resume/achievement/<pk>/save/` | Save bullet |
| POST/DELETE | `/resume/achievement/<pk>/delete/` | Delete bullet |
| POST | `/resume/achievement/<pk>/move/` | Move bullet |
| POST | `/resume/education/add/` | Add education |
| POST | `/resume/education/<pk>/save/` | Save education |
| POST/DELETE | `/resume/education/<pk>/delete/` | Delete education |
| POST | `/resume/education/<pk>/move/` | Move education |
| POST | `/resume/skill/add/` | Add skill |
| POST | `/resume/skill/<pk>/save/` | Save skill |
| POST/DELETE | `/resume/skill/<pk>/delete/` | Delete skill |
| POST | `/resume/skill/<pk>/move/` | Move skill |
| POST | `/resume/certification/add/` | Add certification |
| POST | `/resume/certification/<pk>/save/` | Save certification |
| POST/DELETE | `/resume/certification/<pk>/delete/` | Delete certification |
| POST | `/resume/certification/<pk>/move/` | Move certification |
| GET | `/resume/export/` | Download PDF/DOCX/TXT |
| GET | `/resume/<profile_id>/export/` | Download current-session profile only |
| GET | `/resume/analyze/` | Analyzer page |
| POST | `/resume/analyze/run/` | Analyzer result partial |
| GET | `/resume/action-verbs/<achievement_id>/` | Action verb suggestions |

---

## Invocation Syntax

Local setup:

```powershell
copy .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python manage.py migrate
python manage.py runserver
```

Run checks:

```powershell
python manage.py check
python -m pytest -m "not e2e and not weasyprint"
python -m pytest -m "weasyprint or e2e"
```

`check_production_runtime` requires WeasyPrint native libraries (CI **linux-integration** and Railway release). On Windows without those libs it exits with an error.

```powershell
python manage.py check_production_runtime
python -m ruff check .
python -m black --check .
python -m isort --check-only .
python -m mypy resumes
```

Vendor frontend (after template or pin changes):

```powershell
python scripts/vendor_frontend_assets.py
# Rebuild Tailwind from frontend/ per docs/adr/0010-vendored-frontend-assets.md
```

---

## Input Contract

### Personal info

Fields: `full_name`, `email`, `phone`, `location`, `linkedin_url`, `portfolio_url`.

### Summary

Field: `professional_summary`.

### Theme

Fields:
- `chosen_theme`: `classic`, `modern`, `minimal`
- `accent_color`: `slate`, `blue`, `emerald`, `rose`, `amber`, `violet`, `cyan`, `stone`
- `font_pairing`: `serif`, `sans`, `editorial`, `compact`

### Experience

Fields: `company`, `title`, `location`, `start_date`, `end_date`, `current_role`.

Validation:
- end date must not be before start date
- current role must not have an end date

### Achievement

Field: `text`.

Optional field:
- `replace_with`, used to replace a weak opener with an action verb.

### Education

Fields: `institution`, `degree`, `field`, `start_date`, `end_date`, `gpa`, `notes`.

Validation:
- end date must not be before start date

### Skill

Fields: `name`, `category`, `proficiency`.

Values:
- category: `technical`, `language`, `soft`
- proficiency: 1 through 5

### Certification

Fields: `name`, `issuing_body`, `date_earned`, `expiry`, `credential_id`.

### Analyzer

Field: `jd_text`.

---

## Export Query Parameters

Endpoint:

```text
/resume/export/?format=<format>&theme=<theme>
```

| Parameter | Default | Accepted Values |
|---|---|---|
| `format` | `pdf` | `pdf`, `docx`, `txt` |
| `theme` | profile theme | `classic`, `modern`, `minimal` |

Unsupported format returns HTTP 400.

---

## Output Contract

### `/health/`

```json
{"status": "ok"}
```

### Autosave responses

- HTTP 200
- rendered partial
- `HX-Trigger: resume:saved` when the form is valid, or `resume:invalid` when validation fails
- form errors if invalid
- preview context included

### Export responses

| Format | Content-Type | Filename |
|---|---|---|
| PDF | `application/pdf` | `resume.pdf` |
| DOCX | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | `resume.docx` |
| TXT | `text/plain; charset=utf-8` | `resume.txt` |

All export responses set `Content-Disposition: attachment`.

### Analyzer response

Returns a rendered partial containing present keywords, missing keywords, and match percentage.

---

## Rate Limit Contract

Rate-limited endpoints:
- export
- analyzer run

Rate:

```text
30/hour per session
```

Blocked response:

```text
403
```

---

## Environment Variables

| Variable | Purpose |
|---|---|
| `DJANGO_SETTINGS_MODULE` | settings module |
| `SECRET_KEY` | Django secret; production rejects the dev default `dev-only-change-me` |
| `DEBUG` | debug toggle |
| `DJANGO_READ_DOT_ENV_FILE` | local `.env` loading toggle |
| `SESSION_COOKIE_AGE` | session lifetime |
| `DATABASE_URL` | production database |
| `ALLOWED_HOSTS` | allowed hosts |
| `CSRF_TRUSTED_ORIGINS` | production CSRF origins |
| `SECURE_SSL_REDIRECT` | HTTPS redirect |
| `LOG_LEVEL` | logging level |
| `SENTRY_DSN` | optional Sentry |
| `SENTRY_TRACES_SAMPLE_RATE` | optional Sentry tracing |
| `PORT` | Railway/Gunicorn port |

---

## Side Effects

| Operation | Side Effect |
|---|---|
| first editor visit | creates session and profile |
| autosave | updates profile or child rows |
| add section item | creates ordered row |
| delete section item | deletes row |
| move section item | swaps order values |
| mutation | stores undo snapshot first |
| start over | flushes session |
| undo | restores snapshot and recreates related rows |
| export | generates downloadable bytes |
| analyzer | stores JD text and renders analysis |
| prune command | deletes stale profiles |
| release command | `collectstatic`, migrates, checks WeasyPrint (fails release if unavailable) |

---

## Usage Examples

Open editor:

```text
/resume/edit/
```

Export PDF:

```text
/resume/export/?format=pdf
```

Export DOCX:

```text
/resume/export/?format=docx
```

Export TXT:

```text
/resume/export/?format=txt
```

Run analyzer:

```text
POST /resume/analyze/run/
jd_text=Python Django reporting automation
```

Unsupported export:

```text
/resume/export/?format=csv
```

Expected:

```text
400 Unsupported export format.
```

---

*Constitution reference: Article 4 (input/output boundaries), Article 6 (verification), and Article 8 (understandable and verifiable work).*

---


# Runbook
## App — Resume Builder
**Career Tools Group | Document 4 of 5**

---

## Requirements

Local:
- Python 3.14
- pip and venv
- SQLite
- optional Tailwind standalone binary for CSS rebuilds
- optional WeasyPrint native libraries for full local PDF rendering

Production:
- Railway
- PostgreSQL
- Gunicorn
- WhiteNoise
- Nixpacks native WeasyPrint libraries
- required environment variables
- optional Sentry DSN

---

## Installation

```powershell
copy .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python manage.py migrate
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/resume/edit/
```

---

## Configuration

Local default:

```text
resume_builder.settings.dev
```

Production:

```text
DJANGO_SETTINGS_MODULE=resume_builder.settings.prod
SECRET_KEY=<strong-secret>
DATABASE_URL=<postgres-url>
ALLOWED_HOSTS=<hostnames>
CSRF_TRUSTED_ORIGINS=<origins>
```

Optional:

```text
SENTRY_DSN=<dsn>
LOG_LEVEL=INFO
SENTRY_TRACES_SAMPLE_RATE=0.0
```

---

## Running the App

```powershell
python manage.py runserver
```

Expected:
- `/` redirects to `/resume/edit/`
- `/health/` returns JSON OK
- editor loads
- one profile is created per browser session
- first-visit notice appears once
- autosave updates preview

---

## Running Tests and Checks

Fast suite: ~82 tests locally when WeasyPrint/E2E markers are excluded (full count on Linux CI with integration job).

```powershell
python manage.py check
python -m pytest -m "not e2e and not weasyprint"
python -m pytest -m "weasyprint or e2e"
```

`check_production_runtime` requires WeasyPrint native libraries (CI **linux-integration** and Railway release). On Windows without those libs it exits with an error.

```powershell
python manage.py check_production_runtime
python -m ruff check .
python -m black --check .
python -m isort --check-only .
python -m mypy resumes
```

---

## Rebuilding CSS

```powershell
tailwindcss -i .\assets\tailwind\input.css -o .\static\css\site.css --minify
```

The compiled CSS is committed so the app can run without Node.

---

## Standard Operating Procedures

### Build a resume

1. Open `/resume/edit/`.
2. Enter contact information.
3. Add summary.
4. Add experience and bullets.
5. Add education, skills, and certifications.
6. Select theme/accent/font.
7. Review completeness score and warnings.
8. Export PDF, DOCX, or TXT.

### Undo last change

```text
POST /resume/undo/
```

### Start over

```text
POST /resume/start-over/
```

### Analyze job description

```text
GET /resume/analyze/
POST /resume/analyze/run/
```

### Prune stale profiles

```powershell
python manage.py prune_stale_profiles
```

---

## Deployment

Railway release command:

```text
python manage.py collectstatic --noinput && python manage.py migrate --noinput && python manage.py check_production_runtime
```

Railway start command:

```text
gunicorn resume_builder.wsgi:application --bind 0.0.0.0:$PORT
```

Health check:

```text
/health/
```

Dedicated prune service:

```text
python manage.py prune_stale_profiles
```

Recommended cron:

```text
0 3 * * *
```

---

## Health Checks

### App health

```text
GET /health/
```

Expected:

```json
{"status": "ok"}
```

### Editor health

```text
GET /resume/edit/
```

Expected:
- HTTP 200
- session profile exists
- repeated visit does not create duplicate profile

### Export health

```text
GET /resume/export/?format=pdf
GET /resume/export/?format=docx
GET /resume/export/?format=txt
```

Expected:
- PDF starts with `%PDF-`
- DOCX starts with ZIP bytes
- TXT contains resume text

### Runtime PDF health

```powershell
python manage.py check_production_runtime
```

Expected:

```text
production_runtime weasyprint=available
```

Failed release (WeasyPrint missing):

```text
production_runtime weasyprint=unavailable
WeasyPrint native runtime is unavailable; themed PDF export will not work in production.
```

---

## Known Failure Modes

### PDF fallback

**Trigger:** WeasyPrint native libraries missing.

**Resolution:** Install native libraries or ensure Railway uses `nixpacks.toml`.

### Export/analyzer 403

**Trigger:** Rate limit exceeded.

**Resolution:** Wait for the rate window or intentionally adjust rate settings.

### Resume disappears

**Trigger:** Cookie cleared or session expired.

**Resolution:** Expected design. Recreate resume or use downloaded export.

### Unsupported export format

**Trigger:** `format` not in `pdf`, `docx`, `txt`.

**Resolution:** Use a supported format.

### Foreign profile export

**Trigger:** Trying to export another session's profile ID.

**Resolution:** Use current session export URL.

### Invalid dates

**Trigger:** end date before start date or current role with end date.

**Resolution:** Correct the dates or current role setting.

---

## Troubleshooting Decision Tree

```text
App will not start
  ├── missing dependency?
  │     └── pip install -r requirements-dev.txt
  ├── wrong settings module?
  │     └── use resume_builder.settings.dev locally
  ├── missing DATABASE_URL in prod?
  │     └── configure Railway Postgres
  └── static manifest issue?
        └── run collectstatic

Editor saves fail
  ├── CSRF issue?
  │     └── check token and trusted origins
  ├── no session/profile?
  │     └── check cookies and middleware
  ├── object not owned by session?
  │     └── verify profile filters
  └── form invalid?
        └── inspect returned partial errors

Exports fail
  ├── unsupported format?
  │     └── use pdf/docx/txt
  ├── rate limited?
  │     └── wait
  ├── WeasyPrint native issue?
  │     └── check runtime logs
  └── foreign profile ID?
        └── use current session profile
```

---

## Recovery Procedures

### Bad local database

```powershell
Remove-Item db.sqlite3
python manage.py migrate
```

### Lost session

Expected by design. Use a previous export or rebuild.

### Bad edit

Use undo if a snapshot exists.

### Stale data cleanup

```powershell
python manage.py prune_stale_profiles
```

### Production PDF / failed release

1. Check release logs for `production_runtime weasyprint=unavailable`.
2. Confirm native packages from `nixpacks.toml`.
3. Redeploy.
4. Confirm release succeeds with `production_runtime weasyprint=available`.

---

## Logging Reference

Important messages:
- `production_runtime weasyprint=available`
- `production_runtime weasyprint=unavailable` (release failure)
- `pdf_export renderer=weasyprint theme=... bytes=...`
- `pdf_export renderer=fallback theme=...`
- `prune_stale_profiles deleted=N`

Production logging uses a small JSON formatter with level, logger, message, and exception when present.

---

## Maintenance Notes

- Keep session-only persistence clear to users.
- Keep export as the durable ownership step.
- Add tests before adding new resume sections.
- Preserve object ownership filters in all object-level views.
- Keep rate limits on expensive endpoints.
- Verify WeasyPrint runtime after deployment changes.
- Rebuild vendored frontend assets after template class or JS pin changes.
- Regenerate screenshots after UI changes.
- Keep the web service and prune service separate.

---

*Constitution reference: Article 6 (behavior verification), Article 5 (constraints and trade-offs), and Article 8 (verifiable learner work).*

---


# Lessons Learned
## App — Resume Builder
**Career Tools Group | Document 5 of 5**

---

## Why This Design Was Chosen

This design was chosen because the most useful V1 constraint was one session, one resume, one export. That constraint kept the app from becoming a full SaaS product before the editor and export experience were solid. It also made the data lifecycle easy to explain: the resume lives in the browser session, and downloads are how the user keeps it.

HTMX was a good fit because the app needs immediate feedback but does not need a JavaScript application. Django forms, templates, validation, sessions, and ORM remain the source of truth. HTMX simply gives the page a smoother editing loop.

The normalized model was also worth the extra structure. Even temporary session data benefits from clear relationships and ordering. Experiences have achievements. Skills, education, and certifications have independent order. Exports can read the profile graph directly.

---

## What Was Intentionally Omitted

**Accounts and passwords:** Omitted to keep V1 focused and privacy-light.

**Multiple resumes:** Deferred until account and ownership decisions exist.

**Resume duplication:** Deferred because it depends on multiple resumes.

**Share links:** Deferred because they require token/privacy rules.

**Cover letters:** Separate document workflow, not V1.

**Job tracking:** Would turn the app into a CRM-style product.

**LinkedIn import:** Requires parsing external data and handling import edge cases.

**Analytics:** Deferred to avoid adding tracking/privacy scope.

**Real-time collaboration:** Not needed for a single-user session tool.

**LLM rewriting:** Deferred because deterministic analysis is safer and testable.

---

## Biggest Weakness

The biggest weakness is the session-only persistence model. It is honest and scoped, but users can lose work if they clear cookies, switch devices, or return after session expiry without exporting. The first-visit notice mitigates this, but the app still depends on users understanding that downloads are the durable result.

The second weakness is PDF runtime complexity. WeasyPrint gives high-quality PDF output, but it depends on native libraries. Local fallback PDF prevents complete failure during dev, yet fallback output is intentionally minimal. Production release fails if WeasyPrint is unavailable; Nixpacks and runtime checks reduce but do not eliminate operational concern.

The third weakness is endpoint volume. HTMX autosave is pleasant for users, but it creates many partials and many route handlers. The patterns are consistent, but future growth could make `views.py` too large unless feature areas are split.

---

## Scaling Considerations

If users want accounts:
- add user ownership
- migrate session profiles to user-owned resumes
- add account deletion/privacy rules
- revisit pruning

If multiple resumes are added:
- introduce a `Resume` model
- move child rows under Resume instead of Profile
- add duplicate and dashboard flows

If exports become heavy:
- move PDF generation to background jobs
- cache exports by profile version
- add stronger quota controls

If analyzer quality needs to improve:
- add skill taxonomy
- weight required vs preferred keywords
- group keyword categories
- only add LLM features after privacy and cost decisions

---

## What the Next Refactor Would Be

1. **Centralize HTMX response helpers** so section saves share less repeated code.
2. **Split views by feature area** if the route count continues growing.
3. **Add stronger session-loss reminders** after meaningful edits.
4. **Add export caching** keyed by profile version and format.
5. **Add a profile ownership utility** to reduce repeated `get_object_or_404(..., profile=_profile(request))` patterns.
6. **Formalize theme assets** so preview and PDF templates stay aligned.

---

## What This Project Taught

- **Persistence is product design.** Choosing session-only storage shaped UX, data lifecycle, operations, and scope.
- **HTMX fits server-owned forms.** The app feels interactive without moving truth into JavaScript.
- **Temporary data still deserves structure.** Normalized models made editing and exports cleaner.
- **Export quality is operational.** PDF generation depends on native libraries, logs, release checks, and fallback behavior.
- **Small quality signals matter.** Completeness scoring, bullet warnings, action verbs, and keyword matching provide useful feedback without AI.
- **Rate limits belong in small apps.** Expensive endpoints need guardrails even without accounts.
- **Tests define behavior.** The test suite documents expected behavior for sessions, autosave, exports, analyzer, pruning, undo, ownership, and rate limits.

---

*Constitution v2.0 checklist: This document satisfies Article 5 (trade-off documentation), Article 6 (verification), and Article 7 (progressive complexity) for Resume Builder.*
