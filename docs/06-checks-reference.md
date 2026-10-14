# 06 · Checks reference

Every finding ID chromaverity can emit. IDs are stable: once used, an ID never changes meaning.

## CT1xx · Label lint (one file, tags only)

| ID | Severity | Fires when | What to do |
|---|---|---|---|
| CT101 | warn | Any of primaries, transfer, matrix, range is blank | Set flags at encode time, or use the proposed retag (H.264/HEVC) if you know the right values |
| CT102 | warn | Height ≥ 720 with a BT.601 matrix (`smpte170m`/`bt470bg`) | Check the upstream scaler. SD-to-HD upconverts should convert 601 to 709 too |
| CT103 | info | Height ≤ 576 with a BT.709 **matrix** | Often fine (web downscales); confirm for legacy SD workflows |
| CT104 | warn | PQ/HLG transfer with primaries set to something other than BT.2020 (blank primaries are CT101's job) | One flag was set by hand; HDR deliveries use BT.2020 |
| CT105 | warn | PQ/HLG at 8-bit | HDR10 needs 10-bit; 8-bit HDR bands |
| CT106 | info | BT.2020 primaries with an SDR transfer | Valid wide-gamut SDR, but check whether an HDR transfer flag was lost |
| CT107 | info | PQ with neither mastering display nor content light level on the first frame (HLG needs neither, so it's exempt) | Displays will guess tone mapping; re-attach HDR10 static metadata |
| CT108 | warn | BT.2020 matrix with BT.709 primaries | These come as a set; one was set by hand |
| CT109 | info | `yuvj*` pixel format | FFmpeg's legacy "full range" format; check range after any conversion |

## CT2xx · Label diff (two files)

| ID | Severity | Fires when |
|---|---|---|
| CT201 | warn (dropped/changed), info (added, or pix_fmt/bit depth changes) | One of primaries, transfer, matrix, range, chroma location, pixel format or bit depth differs between before and after |
| CT202 | warn | HDR mastering display or content light level present before, missing after |

## CT3xx · Essence (pixels vs label)

| ID | Severity | Confidence | Fires when |
|---|---|---|---|
| CT300 | info | low | Range check inconclusive (content doesn't reach black/white), or no frames decoded |
| CT301 | error (high conf.) / warn | high / medium / low | Labelled limited, pixels look full |
| CT302 | warn | medium / low | Labelled full, pixels look limited |
| CT303 | warn (looks full) / info (looks limited) | varies | Range not labelled; tells you what the pixels look like |
| CT304 | info | medium | Range label agrees with the pixels |

Method and thresholds: [03 Range detection](03-range-detection.md).

## What to do with a finding

**CT2xx (something changed at a hop).** The fix belongs upstream: whatever made the `after` file should be told the flags explicitly (`-color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv` on FFmpeg, or the equivalent export setting). If you can't re-run the hop, run `chromaverity inspect` on the `after` file: a CT101 there comes with a proposed retag.

**CT3xx (pixels and label disagree).** You get two kinds of proposal, and only someone who knows the file's history can pick:

| If... | Then | Proposal |
|---|---|---|
| The pixels are right and the flag is the lie (most common: a tool wrote the wrong flag or none) | Change the label | **retag**: no re-encode, no quality loss, seconds |
| The label is what the delivery spec demands and the pixels are the lie (a scale step used the wrong range) | Change the pixels | **convert**: re-encode through a `scale` filter. Costs one generation |
| You don't know | Look at a frame. Full-range pixels played as limited look crushed and oversaturated; limited played as full look washed out | Try the retag first (it's reversible: just retag back) |

When `inspect` proposes **two retags** (say `.fullrange.mp4` for CT303 and `.bt709.mp4` for CT101), each fixes one part of the label. Run one, then run `inspect` on its output and apply the other to that. Or merge the two `h264_metadata=` option strings into one command with `:` between them.

**CT300 (inconclusive)** is an honest answer, not a pass. Try `--frames 60`, or a clip with true blacks and whites, before deciding.

## Reserved for the roadmap

| Range | Planned check |
|---|---|
| CT31x | Transfer: PQ/HLG vs SDR from the code-value distribution |
| CT32x | Matrix: BT.601 vs BT.709 from pixels (hard; may become a published negative result) |
| CT33x | Chroma siting |
