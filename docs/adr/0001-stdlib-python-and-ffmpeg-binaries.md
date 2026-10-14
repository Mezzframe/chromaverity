# ADR 0001 · Python stdlib + FFmpeg binaries, no runtime dependencies

**Status:** accepted · 2026-10-13

## Context
chromaverity needs to read labels and measure pixels. Options: Python bindings (PyAV), NumPy/OpenCV for pixel math, or call the `ffprobe`/`ffmpeg` binaries and let FFmpeg's own filters (`signalstats`) do the measuring. Python is the lab's primary language. The tool should install anywhere in one command, including CI runners and archivists' laptops.

## Decision
Use only the Python standard library at runtime and shell out (safely, see `safety.py`) to `ffprobe` and `ffmpeg`. Use FFmpeg filters for measurement. Use `argparse` for the CLI. The MCP SDK is an optional extra.

## Consequences
- Installs with zero dependency resolution; tiny supply-chain surface (SEC spine).
- Measurements match what broadcast engineers already trust (`signalstats`).
- Behavior depends on the user's FFmpeg version. We record it in reports later and test in CI on one pinned version ⟨should⟩.
- Per-pixel work beyond what FFmpeg filters offer (full histograms, learned models) will need NumPy. That will arrive as an optional extra (`[ml]`), not a core dependency.
