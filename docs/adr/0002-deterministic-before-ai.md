# ADR 0002 · Deterministic checks decide; AI explains and ranks

**Status:** accepted · 2026-10-13

## Context
It's tempting to hand a model the ffprobe output and ask "is this right?". The answer would sound confident, vary between runs, and be impossible to audit. Mezzframe's rule is to separate what was measured from what was assumed.

## Decision
- Pass/fail verdicts come from deterministic code with written thresholds and tests.
- Every verdict carries `confidence` and the raw `evidence` behind it.
- Models are welcome to **explain** findings to people (via MCP, the agent does this) and, later, to **classify** where hand rules run out (matrix detection). A learned classifier counts as deterministic for this ADR when its version is pinned, it is evaluated on the zoo, and its results are published with errors.
- "Inconclusive" is a legitimate output and must never be upgraded by a model.

## Consequences
- Reports are reproducible and arguable: anyone can check the numbers.
- The "AI" in v0.1 is the agent interface, not a model inside the tool. That's honest, and it's the right order: the learned checks need the zoo first.
