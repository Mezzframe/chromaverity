"""Read a file's color label with ffprobe.

The command we build, piece by piece (docs/04-cli-anatomy.md goes deeper):

    ffprobe                       the program
      -v error                    only print real errors on stderr
      -protocol_whitelist file    nested references may only be local files
      -select_streams v:0         first video stream only
      -show_streams               dump stream fields (where the color tags live)
      -show_frames                dump per-frame info ...
      -read_intervals %+#1        ... but only for the first frame (side data)
      -of json                    machine-readable output
      file:/abs/path.mp4          the input, forced to the file protocol

Why the first frame too: HDR side data (mastering display, content light
level) is attached to frames, not the stream header.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from chromaverity.safety import INPUT_GUARDS, ffmpeg_input, require_binary, run
from chromaverity.tags import ColorTags


def ffprobe_json(path: Path) -> dict[str, Any]:
    cmd = [
        require_binary("ffprobe"),
        "-v", "error",
        *INPUT_GUARDS,                  # local files only, known containers only (safety.py)
        "-select_streams", "v:0",
        "-show_streams",
        "-show_format",                 # for the duration, when the stream doesn't carry one
        "-show_frames",
        "-read_intervals", "%+#1",
        "-of", "json",
        ffmpeg_input(path),
    ]
    proc = run(cmd)
    return json.loads(proc.stdout or "{}")


def read_tags(path: Path) -> ColorTags:
    """Return the color label of the first video stream in `path`."""
    return tags_from_probe(ffprobe_json(path))


def read_tags_and_duration(path: Path) -> tuple[ColorTags, float | None]:
    """One ffprobe call for both; the sampler uses the duration to spread its frames."""
    data = ffprobe_json(path)
    return tags_from_probe(data), duration_from_probe(data)


def duration_from_probe(data: dict[str, Any]) -> float | None:
    """Seconds, from the stream if it says, else the container. None if neither does."""
    streams = data.get("streams") or [{}]
    for holder in (streams[0], data.get("format") or {}):
        try:
            value = float(holder.get("duration"))
        except (TypeError, ValueError):
            continue
        if value > 0:
            return value
    return None


def tags_from_probe(data: dict[str, Any]) -> ColorTags:
    """Split out so tests can feed saved ffprobe JSON without running ffprobe."""
    streams = data.get("streams") or []
    if not streams:
        raise ValueError("no video stream found")
    frames = data.get("frames") or []
    return ColorTags.from_ffprobe_stream(streams[0], frames[0] if frames else None)
