"""Layer 1a: rules about one file's label, no pixels involved.

These are the checks an experienced engineer does in their head when they
glance at MediaInfo. They're deterministic, fast, and each one cites the
reason it exists. They are also the part existing tools already cover, so we
keep them short and spend our effort on the essence layer.

Each rule is a small function. To add one: write it, give it the next free
CT1xx id, add a test in tests/test_tags_lint_diff.py, and document it in
docs/06-checks-reference.md.
"""

from __future__ import annotations

from collections.abc import Callable

from chromaverity.findings import Finding, Severity
from chromaverity.tags import ColorTags, friendly

SD_MATRICES = {"bt470bg", "smpte170m"}
HDR_TRANSFERS = {"smpte2084", "arib-std-b67"}

Rule = Callable[[ColorTags], "Finding | None"]


def blank_labels(t: ColorTags) -> Finding | None:
    blank = t.blank_fields()
    core_blank = [b for b in blank if b != "chroma_location"]
    if not core_blank:
        return None
    return Finding(
        id="CT101",
        severity=Severity.WARN,
        title="Color label is incomplete",
        detail=(
            f"These fields are not set: {', '.join(core_blank)}. Each player then guesses, "
            "and browsers, TVs and editing apps guess differently, so the same file "
            "can look different on each."
        ),
        evidence={"blank_fields": blank},
        fix_hint="Set the missing flags at encode time, or retag without re-encoding (see proposed_fixes).",
    )


def hd_with_sd_matrix(t: ColorTags) -> Finding | None:
    if (t.height or 0) >= 720 and t.color_space in SD_MATRICES:
        return Finding(
            id="CT102",
            severity=Severity.WARN,
            title="HD/UHD picture labelled with an SD (BT.601) matrix",
            detail=(
                f"{t.width}x{t.height} with matrix {friendly(t.color_space)}. Almost all HD "
                "content uses BT.709. If the label is wrong, reds and greens shift "
                "(skin tones go slightly orange or green). If the pixels really are 601, "
                "the conversion was skipped somewhere upstream."
            ),
            evidence={"height": t.height, "color_space": t.color_space},
            fix_hint="Check the upstream scaler: an SD-to-HD upconvert should also convert 601 to 709.",
        )
    return None


def sd_with_hd_matrix(t: ColorTags) -> Finding | None:
    if t.height and t.height <= 576 and t.color_space == "bt709":
        return Finding(
            id="CT103",
            severity=Severity.INFO,
            title="SD picture labelled BT.709",
            detail=(
                "Legal, and common for web downscales, but legacy SD gear and some archives "
                "assume BT.601 for SD. Make sure the label matches what the pixels were made as."
            ),
            evidence={"height": t.height, "color_space": t.color_space},
        )
    return None


def hdr_transfer_without_2020(t: ColorTags) -> Finding | None:
    if t.color_transfer in HDR_TRANSFERS and t.color_primaries not in (None, "bt2020"):
        return Finding(
            id="CT104",
            severity=Severity.WARN,
            title="HDR transfer with non-BT.2020 primaries",
            detail=(
                f"Transfer is {friendly(t.color_transfer)} but primaries are "
                f"{friendly(t.color_primaries)}. HDR10 and HLG deliveries use BT.2020 "
                "primaries. A mix like this usually means one flag was set by hand."
            ),
            evidence={"color_transfer": t.color_transfer, "color_primaries": t.color_primaries},
        )
    return None


def hdr_at_8bit(t: ColorTags) -> Finding | None:
    if t.color_transfer in HDR_TRANSFERS and t.bit_depth == 8:
        return Finding(
            id="CT105",
            severity=Severity.WARN,
            title="HDR transfer at 8-bit",
            detail=(
                "PQ and HLG spread a much wider brightness range over the same code values. "
                "At 8-bit that shows up as visible banding. HDR10 requires 10-bit."
            ),
            evidence={"color_transfer": t.color_transfer, "bit_depth": t.bit_depth},
        )
    return None


def wide_gamut_sdr(t: ColorTags) -> Finding | None:
    if t.color_primaries == "bt2020" and t.color_transfer in ("bt709", "bt2020-10", "bt2020-12"):
        return Finding(
            id="CT106",
            severity=Severity.INFO,
            title="BT.2020 primaries with an SDR transfer",
            detail=(
                "Valid (wide-gamut SDR) but uncommon. If this was meant to be HDR, the transfer "
                "flag was lost. If it was meant to be plain HD, the primaries are wrong."
            ),
            evidence={"color_primaries": t.color_primaries, "color_transfer": t.color_transfer},
        )
    return None


def pq_without_static_metadata(t: ColorTags) -> Finding | None:
    if t.color_transfer == "smpte2084" and not (t.has_mastering_display or t.has_content_light_level):
        return Finding(
            id="CT107",
            severity=Severity.INFO,
            title="PQ without HDR10 static metadata",
            detail=(
                "No mastering display or content light level data on the first frame. "
                "Displays fall back to their own tone-mapping guesses. This is the side "
                "data that transcodes drop most often."
            ),
            evidence={
                "has_mastering_display": t.has_mastering_display,
                "has_content_light_level": t.has_content_light_level,
            },
        )
    return None


def mixed_matrix_and_primaries(t: ColorTags) -> Finding | None:
    if t.color_space in ("bt2020nc", "bt2020c") and t.color_primaries == "bt709":
        return Finding(
            id="CT108",
            severity=Severity.WARN,
            title="BT.2020 matrix with BT.709 primaries",
            detail="These come as a set in real pipelines. One of them was probably set by hand.",
            evidence={"color_space": t.color_space, "color_primaries": t.color_primaries},
        )
    return None


def jpeg_pixel_format(t: ColorTags) -> Finding | None:
    if t.pix_fmt and t.pix_fmt.startswith("yuvj"):
        return Finding(
            id="CT109",
            severity=Severity.INFO,
            title="Legacy 'yuvj' pixel format",
            detail=(
                f"{t.pix_fmt} is FFmpeg's old way of saying 'full range'. It's common from "
                "phones, webcams and MJPEG. Downstream filters sometimes treat it "
                "inconsistently, so check range carefully after any conversion."
            ),
            evidence={"pix_fmt": t.pix_fmt},
        )
    return None


RULES: tuple[Rule, ...] = (
    blank_labels,
    hd_with_sd_matrix,
    sd_with_hd_matrix,
    hdr_transfer_without_2020,
    hdr_at_8bit,
    wide_gamut_sdr,
    pq_without_static_metadata,
    mixed_matrix_and_primaries,
    jpeg_pixel_format,
)


def lint(tags: ColorTags) -> list[Finding]:
    return [f for rule in RULES if (f := rule(tags)) is not None]
