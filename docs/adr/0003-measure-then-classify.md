# ADR 0003 · Every pixel check splits into measure and classify

**Status:** accepted · 2026-10-13

## Context
Pixel checks need FFmpeg to decode frames (slow, environment-dependent) and logic to interpret the numbers (fast, the part we iterate on). Mixed together, every test needs FFmpeg and every threshold change needs a real file.

## Decision
Each essence check exposes two functions:
- `sample_*(path, ...) -> list[Stats]`: runs FFmpeg, returns plain numbers. No judgement.
- `classify_*(stats, label, ...) -> Finding`: pure function. No I/O.

## Consequences
- Classifier rules are unit-tested with made-up numbers in milliseconds (`tests/test_range_classifier.py`).
- A learned model can replace a `classify_*` function without touching measurement.
- Saved `Stats` from real files become regression fixtures without shipping the media.
