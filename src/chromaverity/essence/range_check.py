"""Is this video really limited range or full range, whatever the label says?

The idea in one picture (8-bit luma code values):

    0     16                                         235    255
    |#####|------------- nominal picture ------------|######|
     ^ footroom                                       ^ headroom
     0 and 255 are reserved in limited range (SDI timing codes)

Limited ("tv") range puts black at 16 and white at 235. A little overshoot
into the head/footroom is normal in camera and broadcast content. Full ("pc")
range puts black at 0 and white at 255.

So:
  * Labelled limited, but blacks sit near 0 and whites near 255?  The pixels
    are probably full range. A player will stretch them again: crushed
    blacks, clipped whites.
  * Labelled full, but blacks never go below ~16 and whites stop at ~235?
    The pixels are probably limited. A player won't stretch them: the
    classic "washed out" grey-blacks look.

How we measure: FFmpeg's `signalstats` filter, which broadcast engineers
already trust for legal-range QC. Per sampled frame it gives YMIN, YMAX
(darkest and brightest luma) and BRNG (share of pixels outside broadcast
range). We never convert the pixels first, so we see the stored code values.

How sure can we be? Honest answer: it depends on the content. A dark, foggy
shot never reaches either end of the scale, so it tells us nothing. The
classifier says "inconclusive" in that case rather than guessing. See
docs/03-range-detection.md for the thresholds and their failure modes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from chromaverity.findings import Confidence, Finding, Severity
from chromaverity.safety import ffmpeg_input, require_binary, run

# Thresholds in 8-bit code values. Scaled for 10/12-bit by multiplying by
# 2**(bits-8), the same way BT.709/BT.2100 define the 10-bit levels.
DEEP_BLACK = 7       # well below black (16) and below a -2% PLUGE bar (~12)
HOT_WHITE = 248      # above the EBU R 103 +103% limit (~242)
LIMITED_BLACK_BAND = (12, 20)   # where limited-range black really lands after encoding
LIMITED_WHITE_BAND = (228, 240)  # where limited-range white really lands after encoding

DEFAULT_SAMPLE_FRAMES = 24
DEFAULT_SAMPLE_FPS = 1.0


@dataclass
class FrameStats:
    ymin: int
    ymax: int
    brng: float  # as reported by signalstats ⟨verify units: appears to be percent⟩


def sample_luma_stats(
    path: Path, frames: int = DEFAULT_SAMPLE_FRAMES, fps: float = DEFAULT_SAMPLE_FPS
) -> list[FrameStats]:
    """Run signalstats over a spread of frames and parse the results.

    The command, piece by piece:

        ffmpeg -hide_banner -v error -nostdin
          -protocol_whitelist file          only local files, even for nested refs
          -i file:/abs/path                 the input, forced to the file protocol
          -map 0:v:0                        first video stream only
          -vf fps=1,signalstats=stat=brng,metadata=mode=print:file=-
              fps=1          one frame per second, so we sample the whole clip
              signalstats    measure YMIN/YMAX; stat=brng adds the out-of-range %
              metadata=print write those numbers to stdout ("file=-")
          -frames:v 24                      stop after 24 sampled frames
          -f null -                         decode only, write no output file
    """
    cmd = [
        require_binary("ffmpeg"),
        "-hide_banner", "-v", "error", "-nostdin",
        "-protocol_whitelist", "file",
        "-i", ffmpeg_input(path),
        "-map", "0:v:0",
        "-vf", f"fps={fps},signalstats=stat=brng,metadata=mode=print:file=-",
        "-frames:v", str(frames),
        "-f", "null", "-",
    ]
    proc = run(cmd)
    return parse_metadata_print(proc.stdout)


def parse_metadata_print(text: str) -> list[FrameStats]:
    """Parse `metadata=mode=print` output into one FrameStats per frame.

    The output looks like:
        frame:0    pts:0       pts_time:0
        lavfi.signalstats.YMIN=16
        lavfi.signalstats.YMAX=235
        lavfi.signalstats.BRNG=0.15
    """
    out: list[FrameStats] = []
    cur: dict[str, float] = {}

    def flush() -> None:
        if {"YMIN", "YMAX"} <= cur.keys():
            out.append(FrameStats(int(cur["YMIN"]), int(cur["YMAX"]), float(cur.get("BRNG", 0.0))))

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("frame:"):
            flush()
            cur = {}
        elif line.startswith("lavfi.signalstats."):
            key, _, val = line[len("lavfi.signalstats."):].partition("=")
            try:
                cur[key] = float(val)
            except ValueError:
                continue
    flush()
    return out


def classify_range(stats: list[FrameStats], tagged_range: str | None, bit_depth: int | None) -> Finding:
    """Compare measured luma extremes with the range label. Pure function, no I/O.

    Returns exactly one Finding: a mismatch, a consistent result, or an
    honest "inconclusive".
    """
    bits = bit_depth or 8
    s = 2 ** (bits - 8)
    n = len(stats)
    if n == 0:
        return Finding(
            id="CT300", severity=Severity.INFO, confidence=Confidence.LOW,
            title="Range check skipped: no frames decoded",
            detail="FFmpeg returned no frame statistics, so the pixels could not be checked.",
        )

    ymin = min(f.ymin for f in stats)
    ymax = max(f.ymax for f in stats)
    deep_black = sum(f.ymin <= DEEP_BLACK * s for f in stats)
    hot_white = sum(f.ymax >= HOT_WHITE * s for f in stats)
    lim_black = sum(LIMITED_BLACK_BAND[0] * s <= f.ymin <= LIMITED_BLACK_BAND[1] * s for f in stats)
    lim_white = sum(LIMITED_WHITE_BAND[0] * s <= f.ymax <= LIMITED_WHITE_BAND[1] * s for f in stats)
    # Reserved timing-reference codes in limited range: 0 and 255 at 8-bit,
    # 0-3 and 1020-1023 at 10-bit, 0-15 and 4080-4095 at 12-bit.
    reserved_hit = ymin <= s - 1 or ymax >= (1 << bits) - s

    evidence = {
        "frames_sampled": n,
        "bit_depth": bits,
        "luma_min": ymin,
        "luma_max": ymax,
        "frames_deep_black": deep_black,
        "frames_hot_white": hot_white,
        "frames_black_at_limited_level": lim_black,
        "frames_white_at_limited_level": lim_white,
        "reserved_codes_seen": reserved_hit,
        "brng_mean": round(sum(f.brng for f in stats) / n, 4),
        "thresholds_8bit": {
            "deep_black": DEEP_BLACK, "hot_white": HOT_WHITE,
            "limited_black_band": LIMITED_BLACK_BAND, "limited_white_band": LIMITED_WHITE_BAND,
        },
    }

    looks_full = deep_black > 0 or hot_white > 0
    full_conf = (
        Confidence.HIGH if deep_black and hot_white and reserved_hit
        else Confidence.MEDIUM if deep_black and hot_white
        else Confidence.LOW
    )
    # "Looks limited" needs the content to actually reach both ends, at the
    # limited levels, and never beyond them. Otherwise we can't tell.
    looks_limited = not looks_full and lim_black > 0 and lim_white > 0
    lim_conf = Confidence.MEDIUM if min(lim_black, lim_white) >= max(2, n // 4) else Confidence.LOW

    tag = tagged_range  # "tv", "pc" or None

    if tag in ("tv", None) and looks_full:
        if tag is None:
            return Finding(
                id="CT303", severity=Severity.WARN, confidence=full_conf,
                title="Range not labelled; pixels look full range",
                detail=(
                    f"No range flag is set, and luma reaches {ymin}..{ymax}. Most players assume "
                    "limited range when the flag is missing, which would crush blacks and clip whites."
                ),
                evidence=evidence,
                fix_hint="Label it full range (pc), or convert the pixels to limited range.",
            )
        return Finding(
            id="CT301",
            severity=Severity.ERROR if full_conf is Confidence.HIGH else Severity.WARN,
            confidence=full_conf,
            title="Labelled limited range, pixels look full range",
            detail=(
                f"Luma reaches {ymin}..{ymax}"
                + (" including reserved codes (0/255 in 8-bit)" if reserved_hit else "")
                + ". Limited-range black is 16 and white is 235. Players will stretch these "
                "values again: crushed shadows and clipped highlights."
            ),
            evidence=evidence,
            fix_hint="If the pixels are right, retag as full range (no re-encode). If the label is right, convert pixels to limited.",
        )

    if tag in ("pc", None) and looks_limited:
        if tag is None:
            return Finding(
                id="CT303", severity=Severity.INFO, confidence=lim_conf,
                title="Range not labelled; pixels look limited range",
                detail=(
                    f"No range flag is set. Luma sits in {ymin}..{ymax}, which matches limited range. "
                    "Most players will guess limited and get it right, but it's still a guess."
                ),
                evidence=evidence,
                fix_hint="Label it limited range (tv).",
            )
        return Finding(
            id="CT302", severity=Severity.WARN, confidence=lim_conf,
            title="Labelled full range, pixels look limited range",
            detail=(
                f"Blacks bottom out near {ymin} and whites top out near {ymax}, right at the "
                "limited-range levels (16/235). Players won't expand them: expect grey blacks and "
                "dull whites, the 'washed out' look."
            ),
            evidence=evidence,
            fix_hint="If the pixels are right, retag as limited range (no re-encode).",
        )

    if (tag == "pc" and looks_full) or (tag == "tv" and not looks_full and (lim_black or lim_white)):
        return Finding(
            id="CT304", severity=Severity.INFO, confidence=Confidence.MEDIUM,
            title="Range label agrees with the pixels",
            detail=f"Labelled {tag}; luma range {ymin}..{ymax} fits.",
            evidence=evidence,
        )

    return Finding(
        id="CT300", severity=Severity.INFO, confidence=Confidence.LOW,
        title="Range check inconclusive",
        detail=(
            f"Luma range {ymin}..{ymax} doesn't reach far enough toward black or white to tell "
            "limited from full. Common for low-contrast, dark or foggy shots. Try more frames "
            "(--frames) or a clip with true blacks and whites."
        ),
        evidence=evidence,
    )
