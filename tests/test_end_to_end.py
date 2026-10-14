"""Whole-tool tests against the synthetic mislabel zoo (scripts/make_zoo.py).

These are the closest thing to "does it work on real files". Each case's
ground truth is in the zoo manifest, so a failure here means the detector
disagreed with a label we wrote ourselves.
"""

import json
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
