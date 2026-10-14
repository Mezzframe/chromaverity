#!/usr/bin/env python3
"""Build the "mislabel zoo": short synthetic clips with known, deliberate label errors.

Why
---
To test a detector you need ground truth: files where you *know* the label is
wrong and how. Real-world mislabeled files are rare, unlicensed, and you never
know for sure what happened to them. So we make our own:

    known-good pixels  +  a deliberate lie in the label  =  a labelled test case

Every clip comes from FFmpeg's built-in test source (testsrc2) with a pure
white and a pure black box drawn on it, so the range checks always have true
extremes to find. Synthetic sources mean no licensing questions and anyone
can regenerate the exact same set.

This is v0.1 of the zoo: a handful of cases used by the test suite. The plan
(docs/09-mislabel-zoo.md) grows it into a published dataset and benchmark.

Usage:
    python scripts/make_zoo.py OUT_DIR          # build all cases
    python scripts/make_zoo.py OUT_DIR --list   # show cases, build nothing
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

SRC = (
    "testsrc2=size={w}x{h}:rate=25:duration={d},"
    "drawbox=x=0:y=0:w=160:h=160:color=white:t=fill,"
    "drawbox=x=160:y=0:w=160:h=160:color=black:t=fill"
)

# Pixels: always convert RGB to *limited* BT.709 Y'CbCr first, because every
# FFmpeg version agrees on that. For full-range pixels we then stretch the code
# values with plain arithmetic (lutyuv). No range negotiation is involved, so the
# result is the same on FFmpeg 4.4, 6.1 and 9.0 (all three run in CI).
#
# Why not just `scale=out_range=pc`? Older FFmpeg (e.g. 4.4) silently converts
# back to limited when the next filter asks for yuv420p. Our first zoo did that
# and the detector (correctly) called the "good" full-range clip a mislabel.
LIMITED = "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p"
STRETCH_TO_FULL = (
    "lutyuv="
    "y='clip((val-16)*255/219,0,255)':"
    "u='clip((val-128)*255/224+128,0,255)':"
    "v='clip((val-128)*255/224+128,0,255)'"
)
# Wipe the frame's own range tag so the encoder writes no label of its own.
# The label is added afterwards, deliberately, by a bitstream filter.
NO_TAG = "setparams=range=unknown:color_primaries=unknown:color_trc=unknown:colorspace=unknown"

# H.273 code points written by h264_metadata (see docs/04-cli-anatomy.md).
H273 = {"bt709": 1, "smpte170m": 6}

# name -> what the pixels really are, and what the label will say.
# label None = leave that flag unset.
CASES: dict[str, dict] = {
    "good_limited_709":             {"pixels": "tv", "label": {"range": "tv", "matrix": "bt709"}},
    "good_full_709":                {"pixels": "pc", "label": {"range": "pc", "matrix": "bt709"}},
    "full_pixels_labelled_limited": {"pixels": "pc", "label": {"range": "tv", "matrix": "bt709"}},
    "limited_pixels_labelled_full": {"pixels": "tv", "label": {"range": "pc", "matrix": "bt709"}},
    "full_pixels_unlabelled":       {"pixels": "pc", "label": None},
    "hd_labelled_601":              {"pixels": "tv", "label": {"range": "tv", "matrix": "smpte170m"}},
}


def _ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", *args], check=True)


def label_params(label: dict) -> str:
    """Build h264_metadata options for a label. Primaries/transfer are always BT.709 here."""
    return ":".join([
        f"video_full_range_flag={1 if label['range'] == 'pc' else 0}",
        f"colour_primaries={H273['bt709']}",
        f"transfer_characteristics={H273['bt709']}",
        f"matrix_coefficients={H273[label['matrix']]}",
    ])


def build(out: Path, name: str, case: dict, w: int = 1280, h: int = 720, d: int = 2) -> Path:
    dst = out / f"{name}.mp4"
    raw = out / f".{name}.untagged.mp4"
    vf = LIMITED + ("," + STRETCH_TO_FULL if case["pixels"] == "pc" else "") + "," + NO_TAG

    # Pass 1: make the *pixels*, with no label at all.
    _ffmpeg("-f", "lavfi", "-i", SRC.format(w=w, h=h, d=d),
            "-vf", vf, "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", str(raw))

    # Pass 2: write the *label* we want into the bitstream, without re-encoding.
    if case["label"] is None:
        raw.replace(dst)
    else:
        _ffmpeg("-i", str(raw), "-c", "copy", "-bsf:v", f"h264_metadata={label_params(case['label'])}", str(dst))
        raw.unlink()
    return dst


def build_dropped(out: Path) -> Path:
    """A 'hop' that loses the label: copy good_limited_709 and blank its flags."""
    src = out / "good_limited_709.mp4"
    dst = out / "hop_dropped_tags.mp4"
    # 2 = "unspecified" in H.273: this is what a careless hop leaves behind.
    # The -color_* options blank the container's colr box too. Without them
    # FFmpeg 9 copies the source's BT.709 into it and the "hop" drops nothing.
    _ffmpeg("-i", str(src), "-c", "copy",
            "-bsf:v", "h264_metadata=colour_primaries=2:transfer_characteristics=2:matrix_coefficients=2",
            "-color_primaries", "unspecified", "-color_trc", "unspecified", "-colorspace", "unspecified",
            str(dst))
    return dst


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("out", type=Path)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        print(json.dumps(CASES, indent=2))
        return 0
    if not shutil.which("ffmpeg"):
        print("ffmpeg not found on PATH", file=sys.stderr)
        return 3
    a.out.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, case in CASES.items():
        build(a.out, name, case)
        manifest[name] = case
    build_dropped(a.out)
    manifest["hop_dropped_tags"] = {"derived_from": "good_limited_709", "change": "primaries/transfer/matrix blanked"}
    (a.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"built {len(manifest)} clips in {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
