"""Whole-tool tests against the synthetic mislabel zoo (scripts/make_zoo.py).

These are the closest thing to "does it work on real files". Each case's
ground truth is in the zoo manifest, so a failure here means the detector
disagreed with a label we wrote ourselves.
"""

import json
import os
import subprocess
import sys

import pytest

from chromaverity import report
from chromaverity.cli import main

pytestmark = pytest.mark.ffmpeg


def finding_ids(rep) -> set[str]:
    return {f["id"] for f in rep["findings"]}


@pytest.mark.parametrize(
    "clip, expected",
    [
        ("good_limited_709", "CT304"),
        ("good_full_709", "CT304"),
        ("full_pixels_labelled_limited", "CT301"),
        ("limited_pixels_labelled_full", "CT302"),
        ("full_pixels_unlabelled", "CT303"),
    ],
)
def test_range_verdicts_match_ground_truth(zoo, clip, expected):
    rep = report.inspect(zoo / f"{clip}.mp4", frames=4)
    assert expected in finding_ids(rep), json.dumps(rep["findings"], indent=1)


def test_hd_labelled_601_is_linted(zoo):
    assert "CT102" in finding_ids(report.inspect(zoo / "hd_labelled_601.mp4", essence=False))


def test_mislabel_gets_both_fix_options(zoo):
    rep = report.inspect(zoo / "full_pixels_labelled_limited.mp4", frames=4)
    kinds = {x["kind"] for x in rep["proposed_fixes"]}
    assert kinds == {"retag", "convert"}
    assert all(x["command"][:2] == ["ffmpeg", "-n"] for x in rep["proposed_fixes"])


def test_proposed_retag_actually_fixes_the_label(zoo, tmp_path):
    """Run the tool's own proposed command, then re-inspect: the mismatch should be gone."""
    src = tmp_path / "clip.mp4"
    src.write_bytes((zoo / "full_pixels_labelled_limited.mp4").read_bytes())
    rep = report.inspect(src, frames=4)
    retag = next(x for x in rep["proposed_fixes"] if x["kind"] == "retag")
    subprocess.run(retag["command"], check=True, capture_output=True)
    fixed = src.with_name("clip.fullrange.mp4")
    after = report.inspect(fixed, frames=4)
    assert "CT301" not in finding_ids(after)
    assert after["tags"]["color_range"] == "pc"


def test_diff_catches_dropped_tags(zoo):
    rep = report.diff(zoo / "good_limited_709.mp4", zoo / "hop_dropped_tags.mp4")
    dropped = {f["evidence"]["field"] for f in rep["findings"] if f["id"] == "CT201"}
    assert {"color_primaries", "color_transfer", "color_space"} <= dropped


def test_text_output_survives_a_non_unicode_console(zoo, tmp_path):
    """Windows pipes use a legacy code page (cp1252); a Japanese filename must not crash the report."""
    clip = tmp_path / "クリップ.mp4"
    clip.write_bytes((zoo / "full_pixels_unlabelled.mp4").read_bytes())
    env = {**os.environ, "PYTHONIOENCODING": "cp1252"}
    proc = subprocess.run(
        [sys.executable, "-m", "chromaverity", "inspect", str(clip), "--frames", "4", "--fail-on", "never"],
        capture_output=True, env=env,
    )
    assert proc.returncode == 0, proc.stderr.decode("cp1252", "replace")
    assert b"Proposed" in proc.stdout


def test_cli_exit_codes(zoo, capsys):
    assert main(["inspect", str(zoo / "good_limited_709.mp4"), "--frames", "4"]) == 0
    assert main(["inspect", str(zoo / "full_pixels_labelled_limited.mp4"), "--frames", "4"]) == 1
    assert main(["inspect", "http://example.com/x.mp4"]) == 4


def test_cli_json_is_valid(zoo):
    out = subprocess.run(
        [sys.executable, "-m", "chromaverity", "inspect", str(zoo / "good_full_709.mp4"), "--json", "--frames", "2"],
        capture_output=True, text=True, check=True,
    ).stdout
    rep = json.loads(out)
    assert rep["schema_version"] == "0.1"
    assert rep["kind"] == "inspect"


def test_out_pointing_at_an_input_is_refused_and_the_file_is_untouched(zoo, tmp_path):
    clip = tmp_path / "keep.mp4"
    clip.write_bytes((zoo / "good_limited_709.mp4").read_bytes())
    before = clip.read_bytes()
    assert main(["inspect", str(clip), "--frames", "2", "--out", str(clip)]) == 4
    assert clip.read_bytes() == before


def test_unwritable_out_exits_3_not_1(zoo, tmp_path):
    # Exit 1 means "findings"; a missing folder is an error and must not look like one.
    assert main(["inspect", str(zoo / "good_limited_709.mp4"), "--frames", "2",
                 "--out", str(tmp_path / "no_such_dir" / "r.json")]) == 3


def test_fail_on_levels(zoo):
    good = str(zoo / "good_limited_709.mp4")
    bad = str(zoo / "full_pixels_labelled_limited.mp4")
    assert main(["inspect", good, "--frames", "2", "--fail-on", "info"]) == 1   # CT304 is info
    assert main(["inspect", bad, "--frames", "2", "--fail-on", "never"]) == 0


def test_diff_exit_codes(zoo):
    args = ["diff", str(zoo / "good_limited_709.mp4"), str(zoo / "hop_dropped_tags.mp4")]
    assert main(args) == 0                        # CT201 is warn; default --fail-on is error
    assert main([*args, "--fail-on", "warn"]) == 1


def test_mcp_accepts_bare_filenames_relative_to_root(zoo):
    pytest.importorskip("mcp")
    import asyncio

    from chromaverity.mcp_server import build_server

    server = build_server(zoo)
    ok = asyncio.run(server.call_tool("chromaverity_inspect", {"path": "good_limited_709.mp4", "frames": 2}))
    assert "CT304" in str(ok)
    refused = asyncio.run(server.call_tool("chromaverity_inspect", {"path": "../outside.mp4"}))
    assert "outside the allowed folder" in str(refused) or "does not exist" in str(refused)


def test_a_black_leader_does_not_hide_a_full_range_body(zoo, tmp_path):
    """40 s clip: 30 s of limited-level black, then 10 s of full-range picture, labelled limited.

    Sampling only the first N seconds would see black at code 16 and call the
    label fine. Spreading the samples across the clip finds the full-range body.
    (`zoo` is only requested so the test skips cleanly without FFmpeg/libx264.)
    """
    limited = "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p"
    stretch = ("lutyuv=y='clip((val-16)*255/219,0,255)':u='clip((val-128)*255/224+128,0,255)'"
               ":v='clip((val-128)*255/224+128,0,255)'")
    body = ("testsrc2=size=320x180:rate=5:duration=10,"
            "drawbox=x=0:y=0:w=40:h=40:color=white:t=fill,drawbox=x=40:y=0:w=40:h=40:color=black:t=fill")
    raw, clip = tmp_path / "raw.mp4", tmp_path / "leader.mp4"
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-v", "error", "-y",
         "-f", "lavfi", "-i", "color=black:size=320x180:rate=5:duration=30",
         "-f", "lavfi", "-i", body,
         "-filter_complex", f"[0:v]{limited}[a];[1:v]{limited},{stretch}[b];[a][b]concat=n=2:v=1:a=0,"
         "setparams=range=unknown:color_primaries=unknown:color_trc=unknown:colorspace=unknown",
         "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", str(raw)],
        check=True,
    )
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", str(raw), "-c", "copy",
         "-bsf:v", "h264_metadata=video_full_range_flag=0:colour_primaries=1:transfer_characteristics=1"
         ":matrix_coefficients=1", "-color_range", "tv", str(clip)],
        check=True,
    )
    rep = report.inspect(clip, frames=8)
    ct3 = next(f for f in rep["findings"] if f["id"].startswith("CT3"))
    assert ct3["id"] == "CT301", ct3
    assert ct3["evidence"]["sample_fps"] == 0.2  # 8 frames over 40 s
