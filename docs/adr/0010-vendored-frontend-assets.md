# ADR 0010: Vendored Frontend Assets Over Public CDNs

## Status

Accepted

## Decision

Serve Tailwind CSS, HTMX, and Lucide from `resumes/static/resumes/vendor/` via Django static files and WhiteNoise. Pin versions: HTMX 2.0.4, Lucide 0.469.0, Tailwind built from `frontend/input.css`.

**Rejected:** Loading Tailwind, HTMX, and Lucide from public CDNs in `base.html`.

## Consequences

Editor styling and HTMX behavior no longer depend on third-party CDN availability or latency. `collectstatic` includes vendor assets in `STATIC_ROOT` for production. Rebuilding Tailwind after template class changes requires `frontend/` and the Tailwind CLI; `scripts/vendor_frontend_assets.py` re-downloads pinned JavaScript files.
