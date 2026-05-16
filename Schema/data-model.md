# Resume Builder Data Model

This schema folder mirrors the Django models in `resumes/models.py`.

## Entities

### Profile
Session-scoped parent record for one resume. A profile owns personal/contact data, theme settings, job-description analyzer text, and timestamps.

### Experience
Ordered work-history row owned by a profile. Each experience can have many achievement bullets.

### Achievement
Ordered bullet row owned by an experience.

### Education
Ordered education row owned by a profile.

### Skill
Ordered skill row owned by a profile. Category is limited to `technical`, `language`, or `soft`; proficiency is an integer from 1 to 5.

### Certification
Ordered certification row owned by a profile.

## Relationships

```text
Profile 1 -- * Experience 1 -- * Achievement
Profile 1 -- * Education
Profile 1 -- * Skill
Profile 1 -- * Certification
```

## Notes

- Date fields use ISO `YYYY-MM-DD` strings or `null`.
- Timestamp fields use ISO date-time strings.
- The JSON schemas allow partial resume data because the app supports autosaving incomplete drafts during a browser session.
- `resume.schema.json` is the top-level schema for import/export style payloads.
