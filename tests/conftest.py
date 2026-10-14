"""Shared test setup.

Two kinds of test live here:
  * pure tests: feed made-up numbers to the classifiers. Fast, no FFmpeg.
  * ffmpeg tests (marked `ffmpeg`): build the mislabel zoo once per run and
    check the whole tool end to end. Skipped automatically if FFmpeg or
    libx264 is missing, so a contributor without FFmpeg can still run the
    pure tests.
"""

from __future__ import annotations

import functools
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@functools.lru_cache(maxsize=1)
def have_ffmpeg() -> bool:
    """ffmpeg, ffprobe and the libx264 encoder are all on PATH.

    Asked lazily, so `pytest -m "not ffmpeg"` never starts a process.
    """
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        return False
    out = subprocess.run(
        ["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True, timeout=30, check=False
    ).stdout
    return "libx264" in out


# CI sets this. A runner that failed to install FFmpeg would otherwise skip the
# whole end-to-end suite and still show green.
REQUIRE_FFMPEG = os.environ.get("CHROMAVERITY_REQUIRE_FFMPEG") == "1"


@pytest.fixture(scope="session")
def zoo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    if not have_ffmpeg():
        if REQUIRE_FFMPEG:
            pytest.fail("CHROMAVERITY_REQUIRE_FFMPEG=1 but ffmpeg/ffprobe with libx264 is not available")
        pytest.skip("ffmpeg/ffprobe with libx264 not available")
    out = tmp_path_factory.mktemp("zoo")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "make_zoo.py"), str(out)], check=True)
    return out
