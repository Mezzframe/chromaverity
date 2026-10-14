"""Command-line entry point.

    chromaverity inspect FILE [--json] [--frames N] [--no-essence] [--fail-on LEVEL]
    chromaverity diff BEFORE AFTER [--json] [--fail-on LEVEL]
    chromaverity mcp [--root DIR]

Built on argparse from the standard library rather than Click or Typer, so
the tool has zero runtime dependencies besides FFmpeg (docs/adr/0001).

Exit codes, so the tool can gate a pipeline or CI job:
    0  nothing at or above --fail-on (default: error)
    1  findings at or above --fail-on
    3  FFmpeg missing, failed or timed out
    4  refused the input path (see safety.py)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from chromaverity import __version__, report
from chromaverity.report import plain
from chromaverity.safety import ToolError, UnsafeInput, checked_media_path

_LEVELS = {"error": 2, "warn": 1, "info": 0, "never": 99}


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="chromaverity",
        description="Check whether a video's color labels match its pixels.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--json", action="store_true", help="print the JSON report instead of text")
        sp.add_argument("--out", type=Path, help="also write the JSON report to this file")
        sp.add_argument(
            "--fail-on", choices=list(_LEVELS), default="error",
            help="exit 1 if any finding is at or above this level (default: error)",
        )

    sp = sub.add_parser("inspect", help="lint one file's label and check it against the pixels")
    sp.add_argument("file")
    sp.add_argument("--frames", type=int, default=24, help="frames to sample for the pixel checks (default 24)")
    sp.add_argument("--no-essence", action="store_true", help="tags only; skip decoding pixels")
    common(sp)

    sp = sub.add_parser("diff", help="compare the label before and after a hop (transcode, export, upscale)")
    sp.add_argument("before")
    sp.add_argument("after")
    common(sp)

    sp = sub.add_parser("mcp", help="run as an MCP server over stdio (needs the [mcp] extra)")
    sp.add_argument("--root", type=Path, default=Path.cwd(), help="only files under this folder can be inspected")
    return p


def _never_crash_on_output() -> None:
    """Print unencodable characters as '?' instead of crashing.

    On Windows, when output goes to a pipe or a file, Python encodes it with
    the ANSI code page (often cp1252). That can't encode many filenames
    (クリップ.mp4) and would raise UnicodeEncodeError halfway through a report.
    Only the human-readable text is affected: --json output is ASCII (json.dumps
    escapes everything else) and --out always writes UTF-8.
    """
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.cmd != "mcp":  # the MCP server owns stdout for its protocol; leave it alone
        _never_crash_on_output()
    try:
        if args.cmd == "mcp":
            from chromaverity.mcp_server import serve  # imported late: optional dependency
            serve(args.root)
            return 0
        if args.cmd == "inspect":
            rep = report.inspect(
                checked_media_path(args.file),
                frames=max(1, args.frames),
                essence=not args.no_essence,
            )
        else:
            rep = report.diff(checked_media_path(args.before), checked_media_path(args.after))
    except UnsafeInput as exc:
        print(f"chromaverity: refused input: {plain(str(exc))}", file=sys.stderr)
        return 4
    except ToolError as exc:
        print(f"chromaverity: {plain(str(exc))}", file=sys.stderr)
        return 3
    except ValueError as exc:  # e.g. no video stream
        print(f"chromaverity: {plain(str(exc))}", file=sys.stderr)
        return 3

    text = json.dumps(rep, indent=2)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text if args.json else report.to_text(rep))

    worst = rep["summary"]["worst"]
    if worst is not None and _LEVELS[worst] >= _LEVELS[args.fail_on]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
