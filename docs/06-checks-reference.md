# 06 · Checks reference

Every finding ID chromaverity can emit. IDs are stable: once used, an ID never changes meaning.

## CT1xx · Label lint (one file, tags only)

| ID | Severity | Fires when | What to do |
|---|---|---|---|
| CT101 | warn | Any of primaries, transfer, matrix, range is blank | Set flags at encode time, or use the proposed retag (H.264/HEVC) if you know the right values |
| CT102 | warn | Height ≥ 720 with a BT.601 matrix (`smpte170m`/`bt470bg`) | Check the upstream scaler. SD-to-HD upconverts should convert 601 to 709 too |
| CT103 | info | Height ≤ 576 labelled BT.709 | Often fine (web downscales); confirm for legacy SD workflows |
| CT104 | warn | PQ/HLG transfer with non-BT.2020 primaries | One flag was set by hand; HDR deliveries use BT.2020 |
| CT105 | warn | PQ/HLG at 8-bit | HDR10 needs 10-bit; 8-bit HDR bands |
| CT106 | info | BT.2020 primaries with an SDR transfer | Valid wide-gamut SDR, but check whether an HDR transfer flag was lost |
| CT107 | info | PQ without mastering display or content light level on the first frame | Displays will guess tone mapping; re-attach HDR10 static metadata |
| CT108 | warn | BT.2020 matrix with BT.709 primaries | These come as a set; one was set by hand |
| CT109 | info | `yuvj*` pixel format | FFmpeg's legacy "full range" format; check range after any conversion |

## CT2xx · Label diff (two files)

| ID | Severity | Fires when |
|---|---|---|
| CT201 | warn (dropped/changed), info (added, or pix_fmt/bit depth changes) | A label field differs between before and after |
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

## Reserved for the roadmap

| Range | Planned check |
|---|---|
| CT31x | Transfer: PQ/HLG vs SDR from the code-value distribution |
| CT32x | Matrix: BT.601 vs BT.709 from pixels (hard; may become a published negative result) |
| CT33x | Chroma siting |
