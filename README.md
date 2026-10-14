# chromaverity

**Your file says BT.709 limited range. Do the pixels agree?**

chromaverity checks whether a video's color label (primaries, transfer, matrix, range) matches what's actually in the picture. It reads the label, checks it across processing hops, measures the pixels, and tells you where they disagree, how sure it is, and the FFmpeg command that would fix it. It runs from the command line, in CI, or as an MCP tool that AI agents can call to check their own transcodes.

An open tool from the [Mezzframe](https://mezzframe.ai) lab, published from the maintainer's GitHub account (Novapakt) · Encode topic · v0.1 (pre-alpha)

```
$ chromaverity inspect zoo/full_pixels_labelled_limited.mp4
chromaverity 0.1.0.dev0  ·  FFmpeg 9.0.2  ·  zoo/full_pixels_labelled_limited.mp4

  primaries     BT.709 (HD)
  transfer      BT.709 (HD)
  matrix        BT.709 (HD)
  range         limited range (16-235 in 8-bit)
  chroma loc    left (MPEG-2 / H.264 default)
  format        h264 1280x720 yuv420p (8-bit)
  HDR metadata  none

[ERR ] CT301  Labelled limited range, pixels look full range  (confidence: high)
       Luma reaches 0..255 including reserved codes (0/255 in 8-bit). Limited-range black is 16
       and white is 235. Players will stretch these values again: crushed shadows and clipped highlights.
       hint: If the pixels are right, retag as full range (no re-encode). If the label is right, convert pixels to limited.

Proposed (retag, no re-encode): Label the file as full range (pixels unchanged)
  why: Use this if the pixels are correct and only the flag is wrong.
  $ ffmpeg -n -i zoo/full_pixels_labelled_limited.mp4 -map 0 -c copy -bsf:v h264_metadata=video_full_range_flag=1 -color_range pc zoo/full_pixels_labelled_limited.fullrange.mp4

Proposed (convert, re-encodes): Convert the pixels to limited range (label unchanged)
  why: Use this if the delivery spec requires limited range. Costs one encode generation.
  note: libx264 output; swap the encoder and quality settings for your delivery spec
  $ ffmpeg -n -i zoo/full_pixels_labelled_limited.mp4 -map 0 -c copy -vf scale=in_range=full:out_range=limited -c:v libx264 -crf 16 -preset slow -color_range tv zoo/full_pixels_labelled_limited.limited.mp4

Nothing was changed. Review a command, then run it yourself.

1 error · 0 warn · 0 info
```

(Real output from the [mislabel zoo](docs/09-mislabel-zoo.md), FFmpeg 9.0.2. Long lines are wrapped here.)

## Why

Every tool reads the label. Open tools don't check whether the label matches the picture, so a wrong flag turns into washed-out blacks on one screen and crushed shadows on another, and nobody knows which file to blame. Read [docs/00-why.md](docs/00-why.md) for the full story and what already exists.

## Quick start

Needs Python 3.10+ and FFmpeg.

| | Install the tools |
|---|---|
| macOS | `brew install python ffmpeg git` |
| Debian / Ubuntu | `sudo apt install python3 python3-venv git ffmpeg` |
| Windows (PowerShell) | `winget install Python.Python.3.13; winget install Gyan.FFmpeg; winget install Git.Git`, then open a new terminal |

Then, on **macOS / Linux**:

```bash
git clone https://github.com/Novapakt/chromaverity.git && cd chromaverity
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,mcp]"
python scripts/make_zoo.py samples      # build synthetic test clips with known mislabels
chromaverity inspect samples/full_pixels_labelled_limited.mp4
chromaverity diff samples/good_limited_709.mp4 samples/hop_dropped_tags.mp4
pytest                                  # the test suite; pure tests run even without FFmpeg
```

On **Windows** (PowerShell), only the setup lines differ. The `make_zoo`, `chromaverity` and `pytest` lines are the same:

```powershell
git clone https://github.com/Novapakt/chromaverity.git; cd chromaverity
python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -e ".[dev,mcp]"
```

CI runs the full test suite on Linux, macOS and Windows. Full per-system guide, other Linux distros, WSL, cmd.exe and troubleshooting: [docs/install.md](docs/install.md).

## What it checks (v0.1)

| Layer | Checks | IDs |
|---|---|---|
| Label lint | blank flags, HD tagged 601, HDR flag mismatches, HDR at 8-bit, missing HDR10 metadata | CT101-CT109 |
| Label diff | flags dropped, changed or added across a hop; HDR side data dropped | CT201-CT202 |
| **Pixels vs label** | **range: limited vs full, with confidence and evidence** | CT300-CT304 |

Full list: [docs/06-checks-reference.md](docs/06-checks-reference.md). Next up: transfer (PQ vs SDR) and matrix (601 vs 709) from pixels. See [ROADMAP.md](ROADMAP.md).

## For AI agents (MCP)

```bash
chromaverity mcp --root ~/Videos/qc-inbox
```

Gives agents two read-only tools, `chromaverity_inspect` and `chromaverity_diff`, limited to one folder. Fixes come back as text for a person to approve. Setup for Claude Code: [docs/08-claude-code.md](docs/08-claude-code.md).

## Docs

The [docs](docs/README.md) are written to teach, from a color primer through every FFmpeg flag we use to the threat model. Start with the reading path that fits you.

## Security

chromaverity reads files and starts `ffprobe`/`ffmpeg`. It never writes, deletes or runs a fix, never uses a shell, restricts FFmpeg to local files, and times out every call. The MCP server only sees files under `--root`. Threat model: [docs/07-security.md](docs/07-security.md). Report vulnerabilities via [SECURITY.md](SECURITY.md).

## Data and licenses

- Code: Apache-2.0 ([LICENSE](LICENSE)). Docs: CC BY 4.0 ([LICENSE-docs](LICENSE-docs)).
- Test media is generated from FFmpeg's built-in test sources. No third-party footage in the repo.
- No models in v0.1.

## Contributing

Contributions are welcome, from a typo fix to a new pixel check. See [CONTRIBUTING.md](CONTRIBUTING.md). Found a real file chromaverity got wrong? That's our favorite kind of issue ([how to report it](docs/09-mislabel-zoo.md#contributing-a-case)).

## Where next

- Run it on one of your own files and read the `evidence` block in `--json`: the numbers are the point.
- [docs/06](docs/06-checks-reference.md) says what each finding means and what to do about it.
- [ROADMAP.md](ROADMAP.md) has what's coming; the [work orders](docs/work-orders/) show how maintenance gets done here.
