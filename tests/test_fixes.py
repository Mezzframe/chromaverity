"""Proposed fixes on made-up findings. No FFmpeg needed.

propose() only builds command lists; nothing here runs them. The tests pin
down which fix appears for which finding, and that nothing from the file's
own metadata can leak into a command.
"""

from pathlib import Path

import pytest

from chromaverity.findings import Confidence, Finding, Severity
from chromaverity.fixes import propose
from chromaverity.tags import ColorTags

SRC = Path("/clips/a.mp4")


def finding(fid: str, **evidence) -> Finding:
    return Finding(id=fid, severity=Severity.WARN, title="t", detail="d", evidence=evidence,
                   confidence=Confidence.MEDIUM)


def h264(**overrides) -> ColorTags:
    t = dict(color_primaries="bt709", color_transfer="bt709", color_space="bt709", color_range="tv",
             pix_fmt="yuv420p", bit_depth=8, width=1920, height=1080, codec="h264")
    t.update(overrides)
    return ColorTags(**t)


def kinds(fixes) -> list[tuple[str, str]]:
    return [(f.for_finding, f.kind) for f in fixes]


def test_full_pixels_labelled_limited_gets_both_options():
    fixes = propose(SRC, h264(), [finding("CT301")])
    assert kinds(fixes) == [("CT301", "retag"), ("CT301", "convert")]
    retag, convert = fixes
    assert "video_full_range_flag=1" in " ".join(retag.command) and "-color_range" in retag.command
    assert not retag.reencode and convert.reencode
    assert "scale=in_range=full:out_range=limited" in convert.command


def test_limited_pixels_labelled_full_gets_a_retag():
    fixes = propose(SRC, h264(color_range="pc"), [finding("CT302")])
    assert kinds(fixes) == [("CT302", "retag")]
    assert "h264_metadata=video_full_range_flag=0" in fixes[0].command


@pytest.mark.parametrize("looks_full, expected", [(True, "fullrange"), (False, "limitedrange")])
def test_unlabelled_range_reads_the_evidence_not_the_title(looks_full, expected):
    fixes = propose(SRC, h264(color_range=None), [finding("CT303", looks_full=looks_full)])
    assert fixes and fixes[0].for_finding == "CT303"
    assert fixes[0].command[-1].endswith(f".{expected}.mp4")


def test_blank_hd_label_is_filled_with_bt709():
    tags = h264(color_primaries=None, color_transfer=None, color_space=None)
    fixes = propose(SRC, tags, [finding("CT101")])
    assert kinds(fixes) == [("CT101", "retag")]
    bsf = next(a for a in fixes[0].command if a.startswith("h264_metadata="))
    assert bsf == "h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1"
    assert fixes[0].command[-1] == str(SRC.with_name("a.bt709.mp4"))


def test_partial_blank_only_fills_the_blanks():
    fixes = propose(SRC, h264(color_space=None), [finding("CT101")])
    bsf = next(a for a in fixes[0].command if a.startswith("h264_metadata="))
    assert bsf == "h264_metadata=matrix_coefficients=1"
    assert "-colorspace" in fixes[0].command and "-color_primaries" not in fixes[0].command


@pytest.mark.parametrize(
    "tags",
    [
        h264(color_primaries="bt2020", color_transfer=None, color_space=None, height=2160, codec="hevc"),
        h264(color_primaries=None, color_transfer="smpte2084", color_space=None, height=2160, codec="hevc"),
        h264(color_primaries=None, color_transfer=None, color_space="bt2020nc", height=2160, codec="hevc"),
        h264(color_primaries=None, color_transfer=None, color_space=None, height=576),  # SD: could be 601
    ],
)
def test_bt709_fill_is_not_offered_for_2020_hdr_or_sd(tags):
    # Writing a 709 matrix under 2020 primaries, or SDR flags onto HDR, would
    # be a new mislabel. SD could be BT.601, so we don't guess there either.
    assert propose(SRC, tags, [finding("CT101")]) == []


def test_codec_without_a_retag_path_gets_a_convert_with_a_note():
    fixes = propose(SRC, h264(codec="prores"), [finding("CT301")])
    assert kinds(fixes) == [("CT301", "convert")]
    assert any("No lossless retag path" in a for a in fixes[0].assumptions)

    fixes = propose(SRC, h264(codec="prores", color_range="pc"), [finding("CT302")])
    assert kinds(fixes) == [("CT302", "convert")]
    assert any("No lossless retag path" in a for a in fixes[0].assumptions)


def test_every_command_refuses_to_overwrite_and_writes_next_to_the_source():
    tags = h264(color_primaries=None, color_transfer=None, color_space=None, color_range=None)
    for fix in propose(SRC, tags, [finding("CT101"), finding("CT303", looks_full=True)]):
        assert fix.command[:2] == ["ffmpeg", "-n"]
        out = Path(fix.command[-1])
        assert out.parent == SRC.parent and out != SRC
        assert fix.command_text and fix.command_text_powershell


def test_metadata_strings_never_reach_a_command():
    """Tag values come from the file. Even crafted ones must not appear in what we tell people to run."""
    evil = "$(rm -rf ~); evil"
    tags = h264(codec=evil, pix_fmt=evil, color_range=None, chroma_location=evil)
    findings = [finding("CT101"), finding("CT303", looks_full=True), finding("CT301")]
    for fix in propose(SRC, tags, findings):
        assert all(evil not in arg for arg in fix.command)
        assert evil not in fix.command_text
