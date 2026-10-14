"""Running ffmpeg/ffprobe on files we don't trust.

Why this module exists
----------------------
Every media file is untrusted input. That's the Mezzframe rule (treat every
input as data, never instructions) and it matters here in two concrete ways:

1. **FFmpeg parsers are big C code.** Malformed files have crashed or hung
   them before. So every call gets a timeout, and we never run them through a
   shell, which would let a crafted filename like `x.mp4; rm -rf ~` run.

2. **FFmpeg "filenames" are really URLs.** `ffprobe http://...` fetches from
   the network. `concat:a|b` and HLS playlists can make it open *other*
   files. A file handed to us by an agent or a stranger could use that to
   read things it shouldn't. We close that door by:
     - resolving the path ourselves and requiring a regular file,
     - prefixing it with `file:` so FFmpeg can't read it as another protocol,
     - passing `-protocol_whitelist file` so nested references can't
       reach the network either,
     - passing `-format_whitelist` with the containers we support, so a
       playlist (HLS, DASH, concat) dressed up as a media file can't make
       FFmpeg open *other local files* for us. `-protocol_whitelist file`
       alone still allows that, because the playlist's entries are files
       too (measured on FFmpeg 9.0.2 with an `.m3u8` under `--root`).

Broadcast analogy: this is the router's lock-out. The operator can only
take the sources they're cleared for, no matter what the panel label says.

See docs/07-security.md for the full threat model.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Generous for a 4K file on a laptop, short enough that a hung parser can't
# stall an agent forever. Override with CHROMAVERITY_TIMEOUT (seconds).
_FALLBACK_TIMEOUT = 120.0


def _timeout_from_env() -> float:
    raw = os.environ.get("CHROMAVERITY_TIMEOUT")
    if raw is None:
        return _FALLBACK_TIMEOUT
    try:
        value = float(raw)
    except ValueError:
        value = float("nan")
    if not value > 0:  # also catches nan
        sys.stderr.write(f"chromaverity: ignoring CHROMAVERITY_TIMEOUT={raw!r}; using {_FALLBACK_TIMEOUT:.0f}s\n")
        return _FALLBACK_TIMEOUT
    return value


DEFAULT_TIMEOUT = _timeout_from_env()

# Container formats we read. Anything else is refused by FFmpeg before it
# parses a byte. Playlist "formats" (hls, dash, concat) are deliberately
# absent: they tell FFmpeg to go and open more files. Names come from
# `ffmpeg -demuxers` (the mov entry covers mp4/m4a/3gp/mj2; matroska covers webm).
FORMAT_WHITELIST = "mov,mp4,m4a,3gp,3g2,mj2,matroska,webm,mxf,mpegts,avi,mpeg,flv"

# Put these before `-i` on every ffmpeg/ffprobe call. One place, so the two
# callers (probe.py and the essence samplers) can't drift apart.
INPUT_GUARDS: list[str] = [
    "-protocol_whitelist", "file",
    "-format_whitelist", FORMAT_WHITELIST,
]


class ToolError(RuntimeError):
    """ffmpeg/ffprobe is missing, failed, or timed out."""


class UnsafeInput(ValueError):
    """The path given to us isn't something we'll open."""


def require_binary(name: str) -> str:
    """Find ffmpeg/ffprobe on PATH or fail with a message a beginner can act on."""
    path = shutil.which(name)
    if path is None:
        raise ToolError(
            f"'{name}' not found on PATH. Install FFmpeg (macOS: `brew install ffmpeg`, "
            f"Ubuntu: `sudo apt install ffmpeg`, Windows: `winget install Gyan.FFmpeg`), open a new "
            f"terminal and try again. More: docs/install.md"
        )
    return path


def checked_media_path(raw: str | os.PathLike[str], allowed_root: Path | None = None) -> Path:
    """Resolve a user/agent-supplied path and refuse anything that isn't a plain file.

    `allowed_root` is used by the MCP server: an agent may only point us at
    files under one folder. The CLI passes None because a person typing a
    path at their own terminal already has access to that file.
    """
    text = os.fspath(raw)
    if "\x00" in text:
        raise UnsafeInput("path contains a NUL byte")
    # A colon before any slash looks like a URL or FFmpeg protocol (http:, concat:).
    # Windows drive letters (C:\) are the one legitimate case.
    head = text.split("/", 1)[0]
    if ":" in head and not (len(head) >= 2 and head[1] == ":" and os.name == "nt"):
        raise UnsafeInput(f"'{text}' looks like a URL or protocol, not a local file")

    path = Path(text).expanduser().resolve(strict=False)
    if allowed_root is not None:
        root = allowed_root.expanduser().resolve()
        if path != root and root not in path.parents:
            raise UnsafeInput(f"'{path}' is outside the allowed folder '{root}'")
    if not path.exists():
        raise UnsafeInput(f"'{path}' does not exist")
    if not path.is_file():
        raise UnsafeInput(f"'{path}' is not a regular file")
    return path


def ffmpeg_input(path: Path) -> str:
    """The string we hand to `-i`: forced through FFmpeg's plain file protocol."""
    return f"file:{path}"


def run(cmd: list[str], timeout: float = DEFAULT_TIMEOUT) -> subprocess.CompletedProcess[str]:
    """Run a command with no shell, a timeout, and a readable error on failure.

    `cmd` is a list, never a string. With a list, each argument reaches the
    program exactly as written, so spaces and semicolons in filenames are
    just characters.

    Output is decoded as UTF-8, which is what ffprobe writes, whatever the
    console's code page is. Without `encoding=`, Windows would decode with
    cp1252 and a stream title like "クリップ" would raise UnicodeDecodeError
    mid-report. `errors="replace"` turns any genuinely broken byte into U+FFFD
    instead of failing. stdin is /dev/null so a child can never read the MCP
    protocol pipe it would otherwise inherit.
    """
    try:
        proc = subprocess.run(  # noqa: S603  (list args, no shell: see docstring)
            cmd,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=timeout,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired as exc:
        raise ToolError(f"{Path(cmd[0]).name} timed out after {timeout:.0f}s") from exc
    if proc.returncode != 0:
        tail = "\n".join(proc.stderr.strip().splitlines()[-5:])
        raise ToolError(f"{Path(cmd[0]).name} exited {proc.returncode}: {tail}")
    return proc
