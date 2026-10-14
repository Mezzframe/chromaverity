# 01 · Color primer

Everything you need to follow the rest of the docs, explained from scratch. If you already live in this world, skim the tables and jump to [02](02-how-it-works.md).

## The pipeline from light to numbers and back

```
 scene light ─► camera RGB ─► transfer (OETF) ─► R'G'B' ─► matrix ─► Y'CbCr ─► quantize ─► code values in the file
                                 "gamma"                     601/709/2020       range: limited or full

 code values ─► de-quantize ─► inverse matrix ─► R'G'B' ─► display EOTF ─► light on screen
                 needs range     needs matrix               needs transfer + primaries
```

The file stores only the code values at the end of the first line. To rebuild the picture, the player needs to know **every choice made on the way in**. Those choices are the label.

## The four flags (plus one)

They're defined in ITU-T H.273 ⟨verify current edition⟩, so H.264, HEVC, AV1 and most containers share the same numbers.

| Flag | ffprobe field | Question it answers | Common values | Gets it wrong → |
|---|---|---|---|---|
| Primaries | `color_primaries` | Which red, green and blue? | `bt709` (HD), `bt2020` (UHD/HDR), `smpte170m`/`bt470bg` (SD) | Saturation off: colors too dull or too vivid |
| Transfer | `color_transfer` | Which brightness curve? | `bt709` (SDR), `smpte2084` (PQ/HDR10), `arib-std-b67` (HLG) | Brightness badly wrong: HDR shown as SDR looks flat and grey |
| Matrix | `color_space` | How was R'G'B' mixed into Y'CbCr? | `bt709`, `smpte170m`/`bt470bg` (BT.601), `bt2020nc` | Subtle hue shift: skin goes slightly orange or green |
| Range | `color_range` | Where do black and white sit? | `tv` (limited), `pc` (full) | Washed out, or crushed shadows and clipped highlights |
| Chroma siting | `chroma_location` | Where do the subsampled color samples sit? | `left`, `topleft` | Faint color fringing on sharp edges |

ffprobe calls the matrix `color_space`, which confuses everyone. In this repo we say **matrix** in prose and keep FFmpeg's field names in code.

## Range, properly

Range is the first flag chromaverity checks against the pixels, so it gets the most detail.

```
 8-bit luma (Y')
 0    16                                                      235   255
 |####|-------------------- picture ---------------------------|#####|
  foot                                                           head
  room                                                           room

 limited ("tv"):  black = 16, white = 235  (chroma 16..240)
 full    ("pc"):  black = 0,  white = 255
```

**Why limited range exists.** Analog video needed room for overshoot from filters and sharpening, and SDI reserves the extreme codes (0 and 255 in 8-bit; 0-3 and 1020-1023 in 10-bit) for timing reference signals. So the picture lives in the middle, with head and footroom on each side. Broadcast and most delivery video is limited range.

**Why full range exists.** Computer graphics, JPEG, many phones and webcams, and screen recordings use all 256 values.

**What a wrong range flag does:**

| Pixels are | Label says | Player does | You see |
|---|---|---|---|
| full | limited | stretches 16..235 to 0..255 again | crushed blacks, clipped whites, contrast too high |
| limited | full | doesn't stretch | grey blacks, dull whites, "washed out" |
| either | nothing | guesses, usually limited | depends on the player: inconsistent across devices |

**10-bit and 12-bit.** Same idea, values scaled. 10-bit limited black is 64 and white 940. 12-bit is 256 and 3760.

## Legal overshoot is normal

Real camera content in limited range dips a little below 16 and peaks a little above 235. EBU R 103 ⟨verify edition⟩ allows roughly -1% to 103%, which is about 14 to 242 in 8-bit. A detector that cries "full range!" whenever it sees 240 would be useless on real broadcast material. chromaverity's thresholds sit outside that window on purpose ([03](03-range-detection.md)).

## Why the label is so fragile

- Flags live in **two places**: the bitstream (H.264/HEVC VUI) and the container (MP4 `colr` box, Matroska elements). Tools disagree about which one wins.
- **Defaults differ.** When a flag is missing, browsers, TVs, NLEs and FFmpeg each make their own guess ⟨verify per player⟩.
- **Every hop rewrites the file.** One forgotten `-color_range` on an encoder and the next hop inherits a blank.
- **Some FFmpeg pixel formats imply range.** `yuvj420p` means "full range" by name, a leftover from JPEG. Filters treat it inconsistently.

## HDR side data

HDR10 adds static metadata beside the four flags: **mastering display** (the grading monitor's primaries and peak brightness) and **content light level** (MaxCLL/MaxFALL). They ride on frames, not in the stream header, and transcodes drop them often. v0.1 records whether they're present and flags a hop that drops them (CT202).

## Further reading

- ITU-T H.273, *Coding-independent code points for video signal type identification* ⟨verify edition⟩
- ITU-R BT.709, BT.601, BT.2020, BT.2100 (free from itu.int)
- EBU R 103, *Video signal tolerance in digital television systems*
- In the Mezzframe study guide: ch. 2 §4, §8-9, §12 (color signalling)
- FFmpeg filter docs for `scale` (`in_range`, `out_range`, `out_color_matrix`) and `signalstats`
