# ADR 0002: HTMX Over A JavaScript Framework

## Status

Accepted

## Decision

Use HTMX for inline saves, partial swaps, and preview refreshes instead of React, Vue, or another client framework.

## Consequences

Django templates remain the source of truth for editor and preview rendering. The server validates and returns partials, which reduces client state and keeps the app small.
