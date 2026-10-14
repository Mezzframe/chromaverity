"""Label parsing, lint rules and hop diffs, from saved ffprobe-shaped data. No FFmpeg needed."""

from chromaverity.diff import diff
from chromaverity.lint import lint
from chromaverity.probe import tags_from_probe
from chromaverity.tags import ColorTags


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
