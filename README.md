# chromaverity

**Your file says BT.709 limited range. Do the pixels agree?**

chromaverity checks whether a video's color label (primaries, transfer, matrix, range) matches what's actually in the picture. It reads the label, checks it across processing hops, measures the pixels, and tells you where they disagree, how sure it is, and the FFmpeg command that would fix it. It runs from the command line, in CI, or as an MCP tool that AI agents can call to check their own transcodes.

An open tool from the [Mezzframe AI](https://mezzframe.ai) lab · Encode topic · v0.1 (pre-alpha)

```
$ chromaverity inspect clip.mp4

  primaries     BT.709 (HD)
  transfer      BT.709 (HD)
  matrix        BT.709 (HD)
  range         limited range (16-235 in 8-bit)
  ...

[ERR ] CT301  Labelled limited range, pixels look full range  (confidence: high)
       Luma reaches 0..255 including reserved codes (0/255 in 8-bit). Limited-range black
       is 16 and white is 235. Players will stretch these values again: crushed shadows
       and clipped highlights.

Proposed (retag, no re-encode): Label the file as full range (pixels unchanged)
  $ ffmpeg -n -i clip.mp4 -map 0 -c copy -bsf:v h264_metadata=video_full_range_flag=1 clip.fullrange.mp4

Nothing was changed. Review a command, then run it yourself.
```

## Why

Every tool reads the label. Open tools don't check whether the label matches the picture, so a wrong flag turns into grey blacks on the web, crushed shadows on a phone, and an afternoon of forum detective work. Read [docs/00-why.md](docs/00-why.md) for the full story and what already exists.

## Quick start

Needs Python 3.10+ and FFmpeg (`brew install ffmpeg` / `sudo apt install ffmpeg`).

```bash
git clone https://github.com/<org>/chromaverity.git && cd chromaverity   # ⟨fill in org⟩
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,mcp]"
python scripts/make_zoo.py samples      # build synthetic test clips with known mislabels
chromaverity inspect samples/full_pixels_labelled_limited.mp4
chromaverity diff samples/good_limited_709.mp4 samples/hop_dropped_tags.mp4
pytest                                  # 36 tests
```

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

## Spine check

| Spine | Depth | Findings (must / should / could) | Decision |
|---|---|---|---|
| NET | lite | n/a: no network access; FFmpeg restricted to `file:` | n/a |
| SEC | standard | must: done (no shell, protocol lock, path gate, timeouts, read-only MCP). should: Dockerfile for untrusted batches; pin dev deps + Dependabot; SBOM at first release | should items in ROADMAP |
| CLOUD/ML | lite | should: record FFmpeg version in reports; publish timing per resolution. could: learned classifier once the zoo is a dataset | deferred to v0.2 |
| DELIVERY | standard | Sprint 1 goal met if CI is green from a clean clone. should: tag v0.1.0 after first public review | pending |

Reviewed: 2026-10-13 · Decided by: Mark
