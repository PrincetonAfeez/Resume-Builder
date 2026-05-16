# ADR 0003: Single App Structure

## Status

Accepted

## Decision

Use one Django app, `resumes`, for the v1 domain.

## Consequences

The app stays easy to navigate. If export code or analyzer code grows beyond service modules, it can be split later without changing the product model.
