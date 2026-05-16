# ADR 0005: Normalized Tables Over JSONField

## Status

Accepted

## Decision

Use normalized tables for experience, achievements, education, skills, and certifications.

## Consequences

Reordering, validation, and targeted HTMX saves are straightforward. JSONField would reduce table count, but it would make section-level validation and updates less explicit.
