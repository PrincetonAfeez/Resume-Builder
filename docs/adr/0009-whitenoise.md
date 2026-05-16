# ADR 0009: WhiteNoise Over S3 For V1

## Status

Accepted

## Decision

Serve static files with WhiteNoise in production.

## Consequences

Deployment stays simple for Railway. S3 or another object store can be introduced later if static asset volume or CDN needs justify it.
