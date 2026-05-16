# ADR 0006: WeasyPrint Over Headless Browser PDF

## Status

Accepted

## Decision

Render PDFs with WeasyPrint.

## Consequences

The export pipeline stays Python-native and testable as a service function. It avoids managing a browser runtime for v1.
