# Schema

Simple JSON Schema files for the Resume Builder project.

## Files

- `resume.schema.json` — top-level resume payload with profile and related sections.
- `profile.schema.json` — session profile, contact fields, theme settings, JD analyzer text, and timestamps.
- `experience.schema.json` — ordered work experience entries.
- `achievement.schema.json` — ordered bullet achievements for an experience.
- `education.schema.json` — ordered education entries.
- `skill.schema.json` — ordered skills with category and proficiency.
- `certification.schema.json` — ordered certifications.
- `sample.resume.json` — small example payload.
- `data-model.md` — human-readable relationship overview.

## Usage

Place this `Schema/` folder in the repository root.

Example validation with Python:

```bash
python -m pip install jsonschema
python - <<'PY'
import json
from pathlib import Path
from jsonschema import Draft202012Validator

schema = json.loads(Path('Schema/resume.schema.json').read_text())
data = json.loads(Path('Schema/sample.resume.json').read_text())
Draft202012Validator.check_schema(schema)
Draft202012Validator(schema).validate(data)
print('sample.resume.json is valid')
PY
```

These schemas are intentionally simple and dependency-free. They document the shape of resume data without changing the existing Django app.
