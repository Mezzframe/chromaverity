"""Label parsing, lint rules and hop diffs, from saved ffprobe-shaped data. No FFmpeg needed."""

import pytest

from chromaverity.diff import diff
from chromaverity.lint import lint
from chromaverity.probe import tags_from_probe
from chromaverity.tags import ColorTags, bit_depth_from_pix_fmt


def probe(**stream) -> dict:
    base = {"codec_name": "h264", "width": 1920, "height": 1080, "pix_fmt": "yuv420p"}
    base.update(stream)
    return {"streams": [base], "frames": []}


def ids(findings) -> set[str]:
    return {f.id for f in findings}


def test_blank_spellings_collapse_to_none():
    t = tags_from_probe(probe(color_primaries="unknown", color_transfer="unspecified", color_space=""))
    assert t.color_primaries is None and t.color_transfer is None and t.color_space is None


def test_bit_depth_from_pix_fmt_when_raw_sample_missing():
    assert tags_from_probe(probe(pix_fmt="yuv420p10le")).bit_depth == 10
    assert tags_from_probe(probe(pix_fmt="yuv420p")).bit_depth == 8


def test_frame_side_data_sets_hdr_flags():
    data = probe(color_transfer="smpte2084")
    data["frames"] = [{"side_data_list": [{"side_data_type": "Mastering display metadata"}]}]
    t = tags_from_probe(data)
    assert t.has_mastering_display and not t.has_content_light_level


def test_clean_hd_label_has_no_findings():
    t = ColorTags("bt709", "bt709", "bt709", "tv", "left", "yuv420p", 8, 1920, 1080, "h264")
    assert lint(t) == []


def test_lint_rules_fire():
    assert "CT101" in ids(lint(ColorTags(height=1080)))
    assert "CT102" in ids(lint(ColorTags("bt709", "bt709", "smpte170m", "tv", height=1080)))
    assert "CT104" in ids(lint(ColorTags("bt709", "smpte2084", "bt709", "tv", height=2160, bit_depth=10)))
    assert "CT105" in ids(lint(ColorTags("bt2020", "smpte2084", "bt2020nc", "tv", height=2160, bit_depth=8)))
    assert "CT107" in ids(lint(ColorTags("bt2020", "smpte2084", "bt2020nc", "tv", height=2160, bit_depth=10)))
    assert "CT109" in ids(lint(ColorTags("bt709", "bt709", "bt709", "pc", pix_fmt="yuvj420p", height=1080)))


def test_diff_flags_dropped_and_changed_fields():
    a = ColorTags("bt709", "bt709", "bt709", "tv", height=1080, has_mastering_display=True)
    b = ColorTags(None, "bt709", "bt470bg", "tv", height=1080)
    found = {(f.id, f.evidence.get("field")): f.severity.value for f in diff(a, b)}
    assert found[("CT201", "color_primaries")] == "warn"
    assert found[("CT201", "color_space")] == "warn"
    assert ("CT202", "has_mastering_display") in found


def test_identical_labels_diff_clean():
    a = ColorTags("bt709", "bt709", "bt709", "tv")
    assert diff(a, a) == []


@pytest.mark.parametrize(
    "pix_fmt, depth",
    [
        ("yuv420p", 8), ("yuvj420p", 8), ("nv12", 8), ("nv21", 8), ("rgb24", 8), ("gray", 8), ("uyvy422", 8),
        ("yuv420p10le", 10), ("yuv422p10be", 10), ("yuv444p12le", 12), ("yuv420p9le", 9), ("yuv422p16le", 16),
        ("gbrp10le", 10), ("gbrap12le", 12), ("yuva444p16le", 16),
        ("p010le", 10), ("p016le", 16), ("p210le", 10), ("p416le", 16), ("nv20le", 10),
        ("gray10le", 10), ("gray12le", 12), ("gray16le", 16), ("ya16le", 16),
        ("v210", 10), ("y210le", 10), ("xv30le", 10), ("xv36le", 12),
        ("x2rgb10le", 10), ("rgb48le", 16), ("bgra64le", 16),
        ("", None),
    ],
)
def test_bit_depth_from_pixel_format_name(pix_fmt, depth):
    # Measured against `ffmpeg -pix_fmts` on 9.0.2. The old "p10 in the name"
    # rule read p010le, gray10le and v210 as 8-bit, which breaks the range thresholds.
    assert bit_depth_from_pix_fmt(pix_fmt) == depth


def test_bits_per_raw_sample_wins_over_the_name():
    assert tags_from_probe(probe(pix_fmt="yuv420p", bits_per_raw_sample="10")).bit_depth == 10
    assert tags_from_probe(probe(pix_fmt="yuv420p10le", bits_per_raw_sample="N/A")).bit_depth == 10


def test_remaining_lint_rules_fire():
    assert "CT103" in ids(lint(ColorTags("bt709", "bt709", "bt709", "tv", height=576)))
    assert "CT106" in ids(lint(ColorTags("bt2020", "bt709", "bt2020nc", "tv", height=2160, bit_depth=10)))
    assert "CT108" in ids(lint(ColorTags("bt709", "bt709", "bt2020nc", "tv", height=1080)))


def test_lint_rules_stay_quiet_when_they_should():
    # SD with a 601 matrix is right, not CT102.
    assert "CT102" not in ids(lint(ColorTags("bt709", "bt709", "smpte170m", "tv", height=576)))
    # HDR transfer with *blank* primaries: CT101 covers the blank; CT104 is for a wrong value.
    found = ids(lint(ColorTags(None, "smpte2084", "bt2020nc", "tv", height=2160, bit_depth=10)))
    assert "CT104" not in found and "CT101" in found
    # 10-bit PQ with both metadata blocks present: no CT105, no CT107.
    clean_hdr = ColorTags("bt2020", "smpte2084", "bt2020nc", "tv", "topleft", "yuv420p10le", 10, 3840, 2160,
                          "hevc", has_mastering_display=True, has_content_light_level=True)
    assert lint(clean_hdr) == []


def test_diff_added_and_format_changes_are_info_without_a_retag_hint():
    a = ColorTags(None, "bt709", "bt709", "tv", pix_fmt="yuv420p10le", bit_depth=10)
    b = ColorTags("bt709", "bt709", "bt709", "tv", pix_fmt="yuv420p", bit_depth=8)
    by_field = {f.evidence["field"]: f for f in diff(a, b)}
    assert by_field["color_primaries"].severity.value == "info"      # added
    assert by_field["color_primaries"].fix_hint is None
    assert by_field["pix_fmt"].severity.value == "info"              # 10-bit master to 8-bit web
    assert by_field["pix_fmt"].fix_hint is None
    assert by_field["bit_depth"].fix_hint is None
    assert "10 -> 8" in by_field["bit_depth"].detail


def test_diff_dropped_content_light_level_is_ct202():
    a = ColorTags("bt2020", "smpte2084", "bt2020nc", "tv", has_content_light_level=True)
    b = ColorTags("bt2020", "smpte2084", "bt2020nc", "tv")
    found = {(f.id, f.evidence.get("field")) for f in diff(a, b)}
    assert ("CT202", "has_content_light_level") in found
