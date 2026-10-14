# 09 · The mislabel zoo

## Idea

To test a detector you need files where you **know** what's wrong. Real mislabelled files are rare, usually not ours to publish, and we can never be sure what happened to them. So we make them:

```
 known-good pixels  +  a deliberate lie in the label  =  a test case with ground truth
```

Because the lie is ours, the ground truth is exact, and we can make as many cases as we want. That's what makes a learned classifier possible later: unlimited labelled training data at zero licensing cost.

## v0.1 (today)

`scripts/make_zoo.py OUT_DIR` builds 7 clips from FFmpeg's `testsrc2` with a pure white and a pure black box, plus a `manifest.json` of truth vs label. Tested in CI on FFmpeg 4.4 and 6.1 (Linux) and 9.0 (macOS, Windows).

| Clip | Pixels | Label | Tests |
|---|---|---|---|
| good_limited_709 | limited | limited | no false alarm |
| good_full_709 | full | full | no false alarm |
| full_pixels_labelled_limited | full | limited | CT301 |
| limited_pixels_labelled_full | limited | full | CT302 |
| full_pixels_unlabelled | full | none | CT303 |
| hd_labelled_601 | limited, BT.709 | limited, BT.601 matrix | CT102 |
| hop_dropped_tags | copy of good_limited_709 | primaries/transfer/matrix blanked | CT201 |

Three lessons found while building it, all exactly the kind of silent behavior this tool exists to catch:

1. **FFmpeg versions disagree about range.** Our first generator used `scale=out_range=pc` to make full-range pixels. On FFmpeg 6.1 that worked. On FFmpeg 4.4 the next filter (`format=yuv420p`) quietly converted the pixels back to limited, so the "good full range" clip was really limited pixels labelled full, and chromaverity flagged it (CT302). The detector was right and our fixture was wrong. The fix: make every clip limited first (all versions agree on that), stretch to full with plain arithmetic (`lutyuv`), and write the label separately with `h264_metadata`. Pixels and label are now set by two independent steps.
2. **Modern FFmpeg copies range from each frame into the encoder**, so leaving out `-color_range` can still produce a labelled file. We wipe frame tags with `setparams` before encoding so the only label is the one we write on purpose.
3. **FFmpeg 9 keeps the old label in the container.** Retagging an already-labelled MP4 with `-c copy -bsf:v h264_metadata=...` changes the H.264 header, but FFmpeg 9.0 writes the input's old values into the MP4 `colr` box, and ffprobe reads that. Our `hop_dropped_tags` clip quietly dropped nothing until CI ran on macOS and Windows (which get FFmpeg 9). Now every retag also passes `-color_range` / `-color_primaries` / `-color_trc` / `-colorspace`, so both places agree. See [04](04-cli-anatomy.md#3-retag-fix-fixespy-proposed-only).

## v0.2 plan: from test set to dataset

| Step | What | Why |
|---|---|---|
| 1 | Swap test patterns for **public-domain footage** (e.g. Prelinger, NASA, Blender open movies ⟨verify licenses per title⟩) | Real content: noise, grading, dark scenes |
| 2 | Generate the **full matrix** of lies: range × matrix × transfer × codec × bit depth | Systematic coverage |
| 3 | Add **realistic hops**: x264, x265, SVT-AV1, ProRes, re-wraps, common cloud-encoder presets | Errors as they happen in the wild |
| 4 | Publish a **benchmark**: accuracy, false alarms, inconclusive rate per check, plus the scripts to rebuild it | Something others can cite and beat |
| 5 | Train the first **learned classifier** (matrix 601 vs 709; this is the v0.3 milestone) and publish results either way | The AI half of the project. Negative results count |

Distribution: generation scripts in this repo (Apache-2.0); generated media published separately with a dataset card (CC BY 4.0, source licenses listed) ⟨verify hosting: GitHub releases vs Hugging Face datasets⟩.

## Contributing a case

Found a real file chromaverity got wrong? Open an issue with the ffprobe output and the report JSON. **Don't attach footage you don't have rights to share.** We'll reproduce the failure synthetically and add it to the zoo.
