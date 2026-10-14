# 02 · How it works

## Three layers

```
                       ┌─────────────────────────────────────────────────────────┐
  media file ─────────►│ LAYER 1 · LABEL      (tags only, no decoding)           │
  (untrusted)          │   probe.py  ffprobe ─► tags.py ColorTags                │
                       │   lint.py   one file:  CT1xx rules                      │
                       │   diff.py   two files: CT2xx changes across a hop       │
                       ├─────────────────────────────────────────────────────────┤
                       │ LAYER 2 · ESSENCE    (decode a sample of frames)        │
                       │   essence/range_check.py                                │
                       │     measure:  ffmpeg signalstats ─► FrameStats          │
                       │     classify: pure function ─► CT3xx + confidence       │
                       ├─────────────────────────────────────────────────────────┤
                       │ LAYER 3 · ASSIST     (proposes, never acts)             │
                       │   fixes.py       FFmpeg commands as text (retag/convert)│
                       │   mcp_server.py  agents call inspect/diff, read-only    │
                       └──────────────────────────┬──────────────────────────────┘
                                                  ▼
                                  report.py ─► JSON report (the product)
                                       │
                         ┌─────────────┴─────────────┐
                    cli.py text view            MCP tool result
```

**Layer 1** is what existing tools do. It's fast and certain about what the label *says*.

**Layer 2** is why the repo exists. It decodes a sample of frames and asks whether the pixels agree with the label. Every check here is split into **measure** (an FFmpeg filter, deterministic) and **classify** (a pure Python function, unit-tested with made-up numbers). That split is what lets us swap a hand-tuned classifier for a learned one later without touching measurement ([ADR 0003](adr/0003-measure-then-classify.md)).

**Layer 3** turns findings into something a person or agent can act on, but stops at a proposal. No code path in v0.1 modifies a file.

## Module map

| Module | One job | Talks to |
|---|---|---|
| `safety.py` | Gate every path and every subprocess (no shell, timeouts, `file:` only) | OS, FFmpeg |
| `probe.py` | Run ffprobe once, return its JSON | safety |
| `tags.py` | Normalise ffprobe's fields into `ColorTags`; blank = `None` | nothing |
| `findings.py` | The one result shape: id, severity, confidence, evidence | nothing |
| `lint.py` | CT1xx rules on one label | tags, findings |
| `diff.py` | CT2xx changes between two labels | tags, findings |
| `essence/range_check.py` | Measure luma extremes; classify range (CT3xx) | safety, findings |
| `fixes.py` | Build retag/convert commands (bash and PowerShell quoting), never run them | tags, findings |
| `report.py` | Assemble layers into the JSON report; render text | everything above |
| `cli.py` | argparse front end, exit codes | report, safety |
| `mcp_server.py` | MCP front end for agents, folder-restricted | report, safety |

Rule of thumb for contributors: **only `safety.py` and the `measure` half of essence checks may start a process.** Everything else is pure functions you can test without FFmpeg.

## One `inspect`, step by step

```
chromaverity inspect clip.mp4
  1. cli.py        parse args
  2. safety.py     resolve path, refuse URLs/dirs/missing  ──► exit 4 on refusal
  3. probe.py      ffprobe -show_streams -show_frames (first frame only)
  4. tags.py       ColorTags(primaries, transfer, matrix, range, ...)
  5. lint.py       CT1xx findings
  6. range_check   ffmpeg fps=1,signalstats  ──► 24 × (YMIN, YMAX, BRNG)
                   classify_range(stats, tagged_range, bit_depth) ──► one CT3xx finding
  7. fixes.py      commands for any fixable finding
  8. report.py     JSON report ──► cli prints text (or --json)
  9. cli.py        exit 0 or 1 depending on --fail-on
```

Cost: one ffprobe call plus one ffmpeg decode of ~24 frames at 1 fps. On a laptop that's a second or two for HD ⟨assumption: measure and publish⟩.

## Design choices worth knowing

| Choice | Why | ADR |
|---|---|---|
| Zero runtime dependencies (stdlib + FFmpeg binaries) | Easy to install anywhere, small supply-chain surface | [0001](adr/0001-stdlib-python-and-ffmpeg-binaries.md) |
| Deterministic checks first; AI explains and ranks, never decides alone | Results you can reproduce and argue with | [0002](adr/0002-deterministic-before-ai.md) |
| Measure and classify split | Test classifiers without FFmpeg; swap in learned models later | [0003](adr/0003-measure-then-classify.md) |
| Propose, never apply | Agents propose, humans approve | [0004](adr/0004-propose-never-apply.md) |
| "Inconclusive" is a valid answer | A confident wrong verdict is worse than no verdict | [03](03-range-detection.md) |

## Where to add things

| You want to add... | Put it in | Also update |
|---|---|---|
| A label rule | `lint.py`, next free CT1xx | tests, [06](06-checks-reference.md) |
| A new pixel check (e.g. transfer) | `essence/<name>_check.py` with `sample_*` + `classify_*` | `report.inspect`, tests, a zoo case, a doc like [03](03-range-detection.md) |
| A retag path for another codec | `fixes.RETAG_BSF` | an end-to-end test that runs the command |
| A new report field | `report.py` | [05](05-report-format.md), schema version if it changes meaning |
