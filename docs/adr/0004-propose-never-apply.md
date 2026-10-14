# ADR 0004 · Fixes are proposed as text; no apply path in v0.x

**Status:** accepted · 2026-10-13

## Context
Mezzframe habit from CueSeal: agents propose, humans approve. chromaverity will be called by AI agents. Only the person who knows a file's history can say whether the label or the pixels are wrong, and the two fixes are opposites (retag vs convert).

## Decision
- v0.x emits commands in the report (`proposed_fixes`) and never runs them.
- Commands use `-n` (no overwrite) and write a new file beside the original.
- When both a retag and a convert are plausible, both are proposed with the trade-off stated.
- A future `--apply` needs a dry run, an explicit confirm, and its own ADR.

## Consequences
- Safe to give to an agent with broad autonomy.
- Slightly more friction for people: copy, review, paste. That's the point.
