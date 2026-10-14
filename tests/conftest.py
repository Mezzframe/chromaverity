"""Shared test setup.

Two kinds of test live here:
  * pure tests: feed made-up numbers to the classifiers. Fast, no FFmpeg.
  * ffmpeg tests (marked `ffmpeg`): build the mislabel zoo once per run and
    check the whole tool end to end. Skipped automatically if FFmpeg or
    libx264 is missing, so a contributor without FFmpeg can still run the
    pure tests.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _have_x264() -> bool:
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        return False
    out = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    return "libx264" in out


HAVE_FFMPEG = _have_x264()


@pytest.fixture(scope="session")
def zoo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    if not HAVE_FFMPEG:
        pytest.skip("ffmpeg/ffprobe with libx264 not available")
    out = tmp_path_factory.mktemp("zoo")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "make_zoo.py"), str(out)], check=True)
    return out
