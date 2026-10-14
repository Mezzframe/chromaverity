"""Proposed fixes: commands we print, never run.

Mezzframe habit: agents propose, humans approve ("cue, then seal"). In v0.1
there is no `--apply` at all. The tool writes the exact FFmpeg command into
the report; a person (or an agent with a person's OK) runs it. A future
`--apply` will need a dry run and an explicit confirm (ROADMAP.md).

Two kinds of fix, and the difference matters:

  retag    The pixels are right, the label is wrong. Rewrite the flags in the
           bitstream with a bitstream filter (`-c copy -bsf:v ...`). No
           re-encode, no quality loss, seconds to run. We also pass the same
           values as output options (`-color_range pc` etc.) so the
           container's `colr` box agrees: FFmpeg 9 copies the *input's*
           values into it otherwise, and players and ffprobe read that box
           (measured; see docs/04-cli-anatomy.md).
  convert  The label is right, the pixels are wrong. Re-encode with a scale
           filter that moves the code values. Costs a generation of quality.

We can't know which one you need. Only someone who knows where the file came
from can say. So when both are possible, we propose both and say so.

Every command uses `-n` (never overwrite) and writes a new file next to the
original. The original is never touched (Preserve-topic rule: originals stay
untouched).
"""

from __future__ import annotations

import shlex
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from chromaverity.findings import Finding
from chromaverity.tags import ColorTags

# Bitstream filters that can rewrite the VUI color flags without re-encoding.
# Option names are the same for H.264 and HEVC because both use H.273 codes.
# ⟨verify⟩ av1_metadata and others are planned; test before adding.
RETAG_BSF = {"h264": "h264_metadata", "hevc": "hevc_metadata"}

# H.273 code points for the values we propose. These are the numbers that
# actually sit in the bitstream; ffprobe shows them as names.
H273 = {"bt709": 1, "unspecified": 2}


@dataclass
class ProposedFix:
    for_finding: str
    kind: str  # "retag" or "convert"
    title: str
    why: str
    command: list[str]
    reencode: bool
    assumptions: list[str] = field(default_factory=list)

    @property
    def command_text(self) -> str:
        # shlex.join quotes anything with spaces, so the text is safe to paste.
        return shlex.join(self.command)

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["command_text"] = self.command_text
        return d


def _out_path(src: Path, label: str) -> Path:
    return src.with_name(f"{src.stem}.{label}{src.suffix}")


def _retag(src: Path, tags: ColorTags, params: str, container: list[str], label: str) -> list[str] | None:
    """`params` rewrites the bitstream; `container` sets the same values for the muxer.

    Both are needed. The bitstream filter alone leaves the MP4 `colr` box
    holding the old values (FFmpeg 9.0, measured), so ffprobe still reports
    the old label.
    """
    bsf = RETAG_BSF.get(tags.codec or "")
    if bsf is None:
        return None
    return [
        "ffmpeg", "-n",              # -n: refuse to overwrite an existing file
        "-i", str(src),
        "-map", "0",                 # keep every stream (audio, captions), not just video
        "-c", "copy",                # copy, don't re-encode
        "-bsf:v", f"{bsf}={params}",  # rewrite the flags in the video bitstream
        *container,                  # ... and tell the muxer, so the container agrees
        str(_out_path(src, label)),
    ]


def propose(src: Path, tags: ColorTags, findings: list[Finding]) -> list[ProposedFix]:
    fixes: list[ProposedFix] = []
    ids = {f.id for f in findings}
    no_bsf_note = (
        f"No lossless retag path for codec '{tags.codec}' in v0.1. Re-encode with the "
        "correct -color_range / -colorspace flags instead."
    )

    if "CT301" in ids or ("CT303" in ids and _looks_full(findings)):
        cmd = _retag(src, tags, "video_full_range_flag=1", ["-color_range", "pc"], "fullrange")
        if cmd:
            fixes.append(ProposedFix(
                for_finding="CT301" if "CT301" in ids else "CT303",
                kind="retag", reencode=False,
                title="Label the file as full range (pixels unchanged)",
                why="Use this if the pixels are correct and only the flag is wrong.",
                command=cmd,
            ))
        fixes.append(ProposedFix(
            for_finding="CT301" if "CT301" in ids else "CT303",
            kind="convert", reencode=True,
            title="Convert the pixels to limited range (label unchanged)",
            why="Use this if the delivery spec requires limited range. Costs one encode generation.",
            command=[
                "ffmpeg", "-n", "-i", str(src),
                "-map", "0", "-c", "copy",              # copy everything ...
                "-vf", "scale=in_range=full:out_range=limited",  # ... except video, which we rescale
                "-c:v", "libx264", "-crf", "16", "-preset", "slow",
                "-color_range", "tv",
                str(_out_path(src, "limited")),
            ],
            assumptions=["libx264 output; swap the encoder and quality settings for your delivery spec"],
        ))
        if not cmd:
            fixes[-1].assumptions.append(no_bsf_note)

    if "CT302" in ids or ("CT303" in ids and not _looks_full(findings)):
        cmd = _retag(src, tags, "video_full_range_flag=0", ["-color_range", "tv"], "limitedrange")
        if cmd:
            fixes.append(ProposedFix(
                for_finding="CT302" if "CT302" in ids else "CT303",
                kind="retag", reencode=False,
                title="Label the file as limited range (pixels unchanged)",
                why="The pixels already sit at limited-range levels; only the flag needs to change.",
                command=cmd,
            ))

    if "CT101" in ids and (tags.height or 0) >= 720 and tags.color_transfer not in ("smpte2084", "arib-std-b67"):
        blank = set(tags.blank_fields())
        parts, container = [], []
        if "color_primaries" in blank:
            parts.append(f"colour_primaries={H273['bt709']}")
            container += ["-color_primaries", "bt709"]
        if "color_transfer" in blank:
            parts.append(f"transfer_characteristics={H273['bt709']}")
            container += ["-color_trc", "bt709"]
        if "color_space" in blank:
            parts.append(f"matrix_coefficients={H273['bt709']}")
            container += ["-colorspace", "bt709"]
        if parts:
            cmd = _retag(src, tags, ":".join(parts), container, "bt709")
            if cmd:
                fixes.append(ProposedFix(
                    for_finding="CT101", kind="retag", reencode=False,
                    title="Fill blank labels with BT.709 (pixels unchanged)",
                    why="Most HD SDR content is BT.709. Only use this if you know that's what it was made as.",
                    command=cmd,
                    assumptions=["⟨assumption⟩ the content is HD SDR made in BT.709"],
                ))
    return fixes


def _looks_full(findings: list[Finding]) -> bool:
    return any(f.id == "CT303" and "full" in f.title for f in findings)
