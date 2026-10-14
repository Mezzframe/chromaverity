"""The report envelope: fields every report carries, whatever the check."""

import pytest

from chromaverity import report


@pytest.mark.parametrize(
    "first_line, expected",
    [
        ("ffmpeg version 6.1.1-3ubuntu5 Copyright (c) 2000-2023", "6.1.1-3ubuntu5"),
        ("ffmpeg version n7.1 Copyright", "n7.1"),
        ("garbage", None),
    ],
)
def test_parse_ffmpeg_version(first_line, expected):
    assert report.parse_ffmpeg_version(first_line) == expected


@pytest.mark.ffmpeg
def test_inspect_report_records_ffmpeg_version(zoo):
    rep = report.inspect(zoo / "good_limited_709.mp4", frames=4)
    version = rep["ffmpeg"]["version"]
    assert isinstance(version, str)
    assert version
