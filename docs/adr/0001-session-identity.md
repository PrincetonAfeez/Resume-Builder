# ADR 0001: Session Identity Over Accounts

## Status

Accepted

## Decision

Use the Django session cookie as the user's identity and create one `Profile` row per session key.

## Consequences

The app has no account, login, password reset, or email verification surface. Clearing cookies or session expiry deletes the user's ability to access the profile. PDF, DOCX, and TXT downloads are the persistence model.
