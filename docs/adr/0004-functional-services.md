# ADR 0004: Functional Services

## Status

Accepted

## Decision

Keep domain behavior in type-hinted functions under `resumes/services/`.

## Consequences

Views stay thin, and the highest-value logic can be tested without HTTP. This also keeps the code approachable for a portfolio reader.
