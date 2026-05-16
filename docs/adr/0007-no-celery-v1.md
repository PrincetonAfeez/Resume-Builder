# ADR 0007: No Celery In V1

## Status

Accepted

## Decision

Run exports and analysis synchronously in the web process.

## Consequences

Operational setup stays simple. If exports become slow or traffic grows, the threshold for adding a queue is clear: move long-running export jobs out of the request path.
