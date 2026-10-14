"""The color "label" on a video stream, normalised into one small record.

Why this module exists
----------------------
A video file carries a handful of flags that tell the decoder how to turn
stored numbers (Y'CbCr code values) back into light on a screen. Broadcast
folks know these as the things that make a monitor look "right". The four
that matter most are defined by ITU-T H.273 and show up in ffprobe as:

    color_primaries  which red, green and blue (BT.709, BT.2020, ...)
    color_transfer   the gamma / EOTF curve (BT.709, PQ, HLG, ...)
    color_space      the Y'CbCr matrix (BT.601 vs BT.709 vs BT.2020)
    color_range      limited ("tv", 16-235) or full ("pc", 0-255)

plus chroma_location (where the subsampled chroma sits) and the pixel format.

ffprobe reports them as short strings. Missing values come back absent,
"unknown" or "unspecified", which all mean the same thing to us: the label is
blank and the player will guess. We collapse those into None so the rest of
the code only has one "blank" to check for.

Read docs/01-color-primer.md for the background.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# ffprobe spells "nobody filled this in" several ways. Treat them all as blank.
_BLANK = {None, "", "unknown", "unspecified", "reserved", "N/A"}

# The fields we compare between files. Order matters only for display.
TAG_FIELDS = (
    "color_primaries",
    "color_transfer",
    "color_space",
    "color_range",
    "chroma_location",
    "pix_fmt",
    "bit_depth",
)

# Human names for the most common ffprobe values. Not exhaustive on purpose:
# unknown values are shown as-is rather than guessed at.
FRIENDLY = {
    "bt709": "BT.709 (HD)",
    "bt470bg": "BT.601 625-line (PAL SD)",
    "smpte170m": "BT.601 525-line (NTSC SD)",
    "bt2020": "BT.2020 (UHD / wide gamut)",
    "bt2020nc": "BT.2020 non-constant luminance",
    "bt2020c": "BT.2020 constant luminance",
    "smpte2084": "PQ / SMPTE ST 2084 (HDR10)",
    "arib-std-b67": "HLG / ARIB STD-B67 (HDR)",
    "tv": "limited range (16-235 in 8-bit)",
    "pc": "full range (0-255 in 8-bit)",
    "left": "left (MPEG-2 / H.264 default)",
    "topleft": "top-left (BT.2020 / UHD default)",
}


def _clean(value: Any) -> str | None:
    """Turn ffprobe's many spellings of 'blank' into None."""
    if value in _BLANK:
        return None
    return str(value)


@dataclass
class ColorTags:
    """What a stream *says* about its color. Not what its pixels *are*."""

    color_primaries: str | None = None
    color_transfer: str | None = None
    color_space: str | None = None
    color_range: str | None = None
    chroma_location: str | None = None
    pix_fmt: str | None = None
    bit_depth: int | None = None
    width: int | None = None
    height: int | None = None
    codec: str | None = None
    # HDR side data travels separately from the four flags and is often the
    # first thing a careless transcode drops. We record presence only in v0.1.
    has_mastering_display: bool = False
    has_content_light_level: bool = False
    # Anything odd we noticed while parsing, kept for the report.
    notes: list[str] = field(default_factory=list)

    @classmethod
    def from_ffprobe_stream(
        cls, stream: dict[str, Any], frame: dict[str, Any] | None = None
    ) -> ColorTags:
        """Build from one entry of ffprobe's `streams` list.

        `frame` is optional: the first decoded frame's side data, used for the
        HDR metadata flags. Stream values win; frame values only fill gaps,
        because some containers leave stream fields empty while the bitstream
        itself carries the flags.
        """
        frame = frame or {}

        def pick(key: str) -> str | None:
            return _clean(stream.get(key)) or _clean(frame.get(key))

        side = [sd.get("side_data_type", "") for sd in frame.get("side_data_list", [])]
        tags = cls(
            color_primaries=pick("color_primaries"),
            color_transfer=pick("color_transfer"),
            color_space=pick("color_space"),
            color_range=pick("color_range"),
            chroma_location=pick("chroma_location"),
            pix_fmt=_clean(stream.get("pix_fmt")),
            bit_depth=_bit_depth(stream),
            width=stream.get("width"),
            height=stream.get("height"),
            codec=_clean(stream.get("codec_name")),
            has_mastering_display=any("Mastering display" in s for s in side),
            has_content_light_level=any("Content light level" in s for s in side),
        )
        return tags

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def blank_fields(self) -> list[str]:
        """The four H.273 flags plus chroma location that nobody filled in."""
        core = ("color_primaries", "color_transfer", "color_space", "color_range", "chroma_location")
        return [name for name in core if getattr(self, name) is None]


def _bit_depth(stream: dict[str, Any]) -> int | None:
    """Work out bits per sample.

    ffprobe gives `bits_per_raw_sample` for many codecs but not all. When it's
    missing we read it off the pixel format name (yuv420p10le -> 10). Plain
    names like yuv420p mean 8-bit.
    """
    raw = stream.get("bits_per_raw_sample")
    if raw not in (None, "", "N/A"):
        try:
            return int(raw)
        except (TypeError, ValueError):
            pass
    pix = str(stream.get("pix_fmt") or "")
    for depth in (16, 14, 12, 10, 9):
        if f"p{depth}" in pix:
            return depth
    return 8 if pix else None


def friendly(value: str | None) -> str:
    """Readable name for a tag value, for humans and for agents' explanations."""
    if value is None:
        return "not set"
    return FRIENDLY.get(value, value)
