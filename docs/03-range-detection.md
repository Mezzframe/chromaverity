# 03 · Range detection (the first pixel check)

**Question:** is this video really limited range or full range, whatever the label says?

**Code:** `src/chromaverity/essence/range_check.py` · **Tests:** `tests/test_range_classifier.py` (rules on made-up numbers), `tests/test_end_to_end.py` (the zoo, and a clip with a black leader)

## Method

### Measure

We sample frames across the clip and run FFmpeg's `signalstats` filter, the same measurement broadcast engineers use for legal-range QC. Per frame we keep:

| Value | Meaning |
|---|---|
| `YMIN` | darkest luma code value in the frame |
| `YMAX` | brightest luma code value in the frame |
| `BRNG` | share of pixels outside broadcast range ⟨verify units: appears to be a percentage⟩. Recorded as evidence, not used in the verdict yet |

Two details matter:

1. **No conversion before measuring.** We never let FFmpeg scale or convert the pixels first, so we see the stored code values, not a player's interpretation of them.
2. **Sampling.** We take 24 frames (change with `--frames`) spread evenly across the clip: the `fps` filter is set to `frames / duration`, so a 10-minute programme is sampled every 25 seconds. A leader of bars or black can't carry the verdict on its own (tested with a 30 s black leader). A clip with one bright shot in a long dark programme can still be missed; more frames helps ⟨assumption: a smarter sampler, e.g. scene-change based, is a good contribution⟩. The rate used is in the report as `evidence.sample_fps`.

### Classify

All thresholds are 8-bit code values, scaled by 2^(bits-8) for 10/12-bit.

| Name | Value | Why this number |
|---|---|---|
| `DEEP_BLACK` | ≤ 7 | Below black (16) and below a -2% PLUGE bar (~12). Legal limited-range content rarely goes here |
| `HOT_WHITE` | ≥ 248 | Above the EBU R 103 +103% limit (~242). Legal overshoot rarely goes here |
| Limited black band | 12..20 | Where limited black actually lands after lossy encoding (16 ± noise) |
| Limited white band | 228..240 | Where limited white actually lands after lossy encoding (235 ± noise) |
| Reserved codes | 0 / 255 (8-bit) | Forbidden in limited range: SDI timing reference codes |

### Rules

```
looks_full    = some frames reach DEEP_BLACK  or  some frames reach HOT_WHITE
looks_limited = not looks_full  and  some frames' black sits in the limited black band
                                 and  some frames' white sits in the limited white band

confidence (looks_full):
   both deep black AND hot white AND reserved codes seen  ──► high
   both deep black AND hot white                          ──► medium
   only one side                                          ──► low   (could be crushed shadows
                                                                     or clipped highlights)
confidence (looks_limited):
   both bands hit on ≥ max(2, frames/4) frames  ──► medium
   otherwise                                    ──► low
   (never high: graded content can sit at 16/235 on purpose)

agrees (CT304):
   labelled full     and looks_full
   labelled limited  and not looks_full  and at least ONE band hit
   (one end is enough for a limited label: plenty of limited-range content
    never reaches white, and we only need to see that it isn't full)
```

| Label | Pixels look | Finding | Severity |
|---|---|---|---|
| limited | full | CT301 | error if high confidence, else warn |
| full | limited | CT302 | warn |
| none | full | CT303 | warn |
| none | limited | CT303 | info |
| matches | matches | CT304 | info |
| any | can't tell | CT300 | info, "inconclusive" |

## Measured on the synthetic zoo

`chromaverity inspect --json` on every zoo clip, 2026-10-14, FFmpeg 9.0.2, libx264, CRF 18, 1280×720 test pattern with pure white and black boxes, 24 frames each:

| Clip | Label | Truth | Verdict | Luma min..max |
|---|---|---|---|---|
| good_limited_709 | tv | tv | CT304 agrees, medium | 13..235 |
| good_full_709 | pc | pc | CT304 agrees, medium | 0..255 |
| full_pixels_labelled_limited | tv | pc | **CT301 error, high** | 0..255 |
| limited_pixels_labelled_full | pc | tv | **CT302 warn, medium** | 13..235 |
| full_pixels_unlabelled | none | pc | **CT303 warn, high** | 0..255 |
| hd_labelled_601 | tv | tv | CT304 agrees, medium (the mislabel here is the matrix: CT102) | 13..235 |
| hop_dropped_tags | tv | tv | CT304 agrees, medium (the mislabel here is the dropped flags: CT201 in `diff`) | 13..235 |

Black lands at 13, not 16: that's lossy encoding noise, and exactly why the limited black band is 12..20 rather than a single value.

**What this does not show.** Synthetic test patterns have perfect blacks and whites in every frame, which is the easiest possible case. Real footage is harder. We haven't measured accuracy on real content yet; that's the job of the [mislabel zoo](09-mislabel-zoo.md) v0.2. Every report records which FFmpeg produced it (`ffmpeg.version`), so results from different machines can be compared fairly.

## Where it fails (on purpose, and not)

| Content | What happens | Why |
|---|---|---|
| Low-contrast, dark, foggy shots | CT300 inconclusive | Never reaches either end of the scale. Correct behavior |
| Graded with lifted blacks and rolled-off whites, labelled full | CT302 false alarm possible | Looks exactly like limited. Medium confidence at most |
| Limited content with heavy illegal overshoot (bad camera settings) | CT301 false alarm possible, usually low/medium | The pixels really are out of range; arguably worth flagging anyway |
| Letterboxed/pillarboxed content | Black bars help find black level | Bars are usually true black |
| Full range with crushed blacks only | CT301 low confidence | One-sided evidence |

## Ideas for v0.2+

- Use the full luma histogram, not only per-frame min/max (pile-ups at 16 and 235 are a strong limited-range fingerprint).
- Use chroma: limited chroma sits in 16..240.
- Scene-aware sampling.
- Learn the thresholds from the zoo instead of hand-setting them, and publish the ROC curve.
