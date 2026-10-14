"""Proposed fixes must paste correctly into bash/zsh *and* PowerShell.

The pure tests pin the quoting rules. The round-trip test is the real proof:
it hands a PowerShell-quoted command to `pwsh` and checks every argument
arrives unchanged. It runs wherever PowerShell 7 is installed (all GitHub
runners have it) and skips elsewhere.
"""

import json
import shutil
import subprocess
import sys

import pytest

from chromaverity.fixes import powershell_join, powershell_quote

# Things real filenames contain, plus things that would break a naive quote.
AWKWARD = [
    "plain.mp4",
    "my clip.mp4",
    "it's.mp4",
    "it\u2019s.mp4",          # typographic apostrophe: PowerShell treats it as a quote
    "$HOME.mp4",
    "a;b.mp4",
    "fps=1,signalstats",       # comma: PowerShell would split it into an array
    "@splat.mp4",
    "#hash.mp4",
    "(x).mp4",
    "back`tick.mp4",
    "~/clips/a.mp4",
    "C:\\Users\\me\\My Videos\\clip.mp4",
    "caf\u00e9.mp4",
]


def test_safe_arguments_stay_bare():
    for arg in ["ffmpeg", "-n", "-c:v", "0", "h264_metadata=video_full_range_flag=1", "C:\\a\\b.mp4", "./a.mp4"]:
        assert powershell_quote(arg) == arg


def test_unsafe_arguments_get_single_quotes():
    assert powershell_quote("my clip.mp4") == "'my clip.mp4'"
    assert powershell_quote("it's.mp4") == "'it''s.mp4'"
    assert powershell_quote("$HOME") == "'$HOME'"
    assert powershell_quote("a,b") == "'a,b'"
    assert powershell_quote("") == "''"


def test_quoted_program_gets_call_operator():
    assert powershell_join(["C:\\Program Files\\ffmpeg.exe", "-n"]) == "& 'C:\\Program Files\\ffmpeg.exe' -n"
    assert powershell_join(["ffmpeg", "-n"]) == "ffmpeg -n"


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="PowerShell 7 (pwsh) not installed")
def test_powershell_round_trip():
    echo = [sys.executable, "-c", "import sys, json; print(json.dumps(sys.argv[1:]))"]
    line = powershell_join(echo + AWKWARD)
    out = subprocess.run(
        ["pwsh", "-NoProfile", "-NonInteractive", "-Command", line],
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout
    assert json.loads(out) == AWKWARD
