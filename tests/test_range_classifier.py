"""The range classifier on made-up numbers. No FFmpeg needed.

Each test is one sentence of the rulebook in docs/03-range-detection.md.
If you change a threshold, these tell you exactly which promise you broke.
"""

from chromaverity.essence.range_check import FrameStats, classify_range, parse_metadata_print, sample_fps


def frames(ymin: int, ymax: int, n: int = 6, brng: float = 0.0) -> list[FrameStats]:
    return [FrameStats(ymin, ymax, brng) for _ in range(n)]


def test_full_pixels_labelled_limited_is_error_with_reserved_codes():
    f = classify_range(frames(0, 255), "tv", 8)
    assert f.id == "CT301"
    assert f.severity.value == "error"
    assert f.confidence.value == "high"


def test_full_pixels_without_reserved_codes_is_only_a_warning():
    f = classify_range(frames(3, 252), "tv", 8)
    assert f.id == "CT301"
    assert f.severity.value == "warn"
    assert f.confidence.value == "medium"


def test_one_sided_excursion_is_low_confidence():
    # Deep blacks but normal whites: could be crushed shadows, not full range.
    f = classify_range(frames(2, 230), "tv", 8)
    assert f.id == "CT301"
    assert f.confidence.value == "low"


def test_limited_pixels_labelled_full_is_washed_out_warning():
    f = classify_range(frames(16, 235), "pc", 8)
    assert f.id == "CT302"
    assert f.severity.value == "warn"


def test_legal_overshoot_is_not_called_full_range():
    # Camera content with a little head/footroom use (EBU R 103 allows -1%..103%).
    f = classify_range(frames(14, 242), "tv", 8)
    assert f.id == "CT304"


def test_low_contrast_content_is_inconclusive_not_a_guess():
    f = classify_range(frames(40, 180), "pc", 8)
    assert f.id == "CT300"
    assert f.confidence.value == "low"


def test_unlabelled_full_range_gets_its_own_code():
    f = classify_range(frames(0, 255), None, 8)
    assert f.id == "CT303"
    assert "full" in f.title


def test_ten_bit_thresholds_scale_by_four():
    # 10-bit limited black is 64, white 940. Full uses 0..1023.
    assert classify_range(frames(64, 940), "pc", 10).id == "CT302"
    assert classify_range(frames(0, 1023), "tv", 10).id == "CT301"


def test_no_frames_is_reported_not_crashed():
    assert classify_range([], "tv", 8).id == "CT300"


def test_parse_metadata_print():
    text = (
        "frame:0    pts:0       pts_time:0\n"
        "lavfi.signalstats.YMIN=16\nlavfi.signalstats.YMAX=235\nlavfi.signalstats.BRNG=0.1\n"
        "frame:1    pts:1       pts_time:1\n"
        "lavfi.signalstats.YMIN=0\nlavfi.signalstats.YMAX=255\n"
    )
    out = parse_metadata_print(text)
    assert [(f.ymin, f.ymax) for f in out] == [(16, 235), (0, 255)]
    assert out[1].brng == 0.0


def test_evidence_says_whether_the_pixels_looked_full():
    assert classify_range(frames(0, 255), None, 8).evidence["looks_full"] is True
    assert classify_range(frames(16, 235), None, 8).evidence["looks_full"] is False


def test_sample_fps_spreads_frames_across_the_clip():
    # 24 frames over 10 minutes: one every 25 s. Over 2 s: 12 per second.
    assert sample_fps(24, 600.0) == 0.04
    assert sample_fps(24, 2.0) == 12.0
    # Unknown duration: the old one-per-second behaviour.
    assert sample_fps(24, None) == 1.0
    assert sample_fps(24, 0.0) == 1.0
    # Absurd requests are capped so we don't decode duplicates all day.
    assert sample_fps(240, 0.5) == 30.0


def test_sample_fps_is_recorded_in_the_evidence():
    stats = frames(0, 255)
    for st in stats:
        st.sample_fps = 0.04
    assert classify_range(stats, "tv", 8).evidence["sample_fps"] == 0.04
