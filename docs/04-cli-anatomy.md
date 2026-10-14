# 04 · CLI anatomy

Every command chromaverity runs or proposes, taken apart flag by flag. Learning to read FFmpeg commands this way pays off far beyond this repo.

## How to read any FFmpeg command

FFmpeg arguments are **positional in groups**. Options apply to the next input (`-i`) or output file that follows them:

```
ffmpeg  [global options]  [input options] -i INPUT  [output options] OUTPUT
          -v error          -f lavfi        -i ...     -c:v libx264    out.mp4
          -n / -y
```

Stream specifiers narrow an option to some streams: `-c:v` (video codecs), `-bsf:v` (video bitstream filters), `-map 0:v:0` (input 0, first video stream). `-c copy` with no specifier means "all streams".

Commands below are written for bash/zsh. The `\` at a line end means "continued on the next line". In PowerShell use a backtick `` ` `` instead, in cmd.exe use `^`, or put the command on one line. More shell differences: [install.md](install.md#6-pasting-the-proposed-fixes).

## 1. Reading the label (probe.py)

```bash
ffprobe -v error -protocol_whitelist file -select_streams v:0 \
        -show_streams -show_frames -read_intervals %+#1 -of json file:/abs/clip.mp4
```

| Piece | Type | What it does | Why we use it |
|---|---|---|---|
| `ffprobe` | program | FFmpeg's inspector; reads, doesn't decode the whole file | Cheapest way to see the label |
| `-v error` | global option | Log level: only real errors on stderr | Clean output to parse |
| `-protocol_whitelist file` | input option | Only the local-file protocol may be opened, including nested references | Stops playlists or crafted files from reaching the network ([07](07-security.md)) |
| `-select_streams v:0` | option + stream specifier | First video stream only | Audio and data streams don't carry color tags |
| `-show_streams` | section switch | Print stream-level fields | Where the four flags live |
| `-show_frames` | section switch | Print per-frame fields | HDR side data lives on frames |
| `-read_intervals %+#1` | option, interval syntax | From the start (`%`), read 1 packet/frame (`+#1`) | Don't decode the whole file just for side data |
| `-of json` | output format | Machine-readable output | `json.loads` instead of text scraping |
| `file:/abs/clip.mp4` | input URL | Forces the plain file protocol | A file named `http:...` or `concat:...` can't be read as a URL |

## 2. Measuring the pixels (range_check.py)

```bash
ffmpeg -hide_banner -v error -nostdin -protocol_whitelist file -i file:/abs/clip.mp4 \
       -map 0:v:0 -vf "fps=1,signalstats=stat=brng,metadata=mode=print:file=-" \
       -frames:v 24 -f null -
```

| Piece | Type | What it does |
|---|---|---|
| `-hide_banner` | global | Skip the build banner |
| `-nostdin` | global | Never read the keyboard; FFmpeg otherwise listens for `q`, which can hang a subprocess |
| `-map 0:v:0` | output option | Use only input 0's first video stream |
| `-vf "..."` | output option | A filter chain; filters run left to right, separated by commas |
| `fps=1` | filter | One frame per second, so the sample spans the clip |
| `signalstats=stat=brng` | filter + option | Measures YMIN/YMAX etc.; `stat=brng` adds the out-of-broadcast-range figure |
| `metadata=mode=print:file=-` | filter + options | Print each frame's measurements; `file=-` means stdout |
| `-frames:v 24` | output option | Stop after 24 frames leave the filter chain |
| `-f null -` | output format + "file" | The null muxer: decode and filter, write nothing. `-` is a placeholder name |

Filter option syntax: `filter=key=value:key=value`. The `:` separates options within one filter, `,` separates filters.

## 3. Retag fix (fixes.py, proposed only)

```bash
ffmpeg -n -i clip.mp4 -map 0 -c copy -bsf:v h264_metadata=video_full_range_flag=1 clip.fullrange.mp4
```

| Piece | What it does | Why |
|---|---|---|
| `-n` | Never overwrite; exit if the output exists | The opposite of `-y`. Safe default for anything a person pastes |
| `-map 0` | Keep **all** streams from input 0 | Without it FFmpeg picks one video and one audio stream and silently drops the rest (captions, extra audio) |
| `-c copy` | Stream copy: no decode, no encode | Zero quality loss, seconds to run |
| `-bsf:v h264_metadata=...` | Bitstream filter on video: rewrites H.264 header fields in place | Changes the label without touching the pixels. HEVC uses `hevc_metadata` with the same option names |
| `video_full_range_flag=1` | The H.264 VUI range bit: 1 = full, 0 = limited | |

Other `h264_metadata` options we use: `colour_primaries`, `transfer_characteristics`, `matrix_coefficients`. Values are H.273 numbers: 1 = BT.709, 2 = unspecified, 9 = BT.2020, 16 = PQ, 18 = HLG ⟨verify against H.273 before adding more⟩.

## 4. Convert fix (fixes.py, proposed only)

```bash
ffmpeg -n -i clip.mp4 -map 0 -c copy -vf scale=in_range=full:out_range=limited \
       -c:v libx264 -crf 16 -preset slow -color_range tv clip.limited.mp4
```

| Piece | What it does |
|---|---|
| `-c copy` then `-c:v libx264` | Copy every stream, then override the video stream to re-encode. Later, more specific options win |
| `scale=in_range=full:out_range=limited` | Rescale code values 0..255 to 16..235 |
| `-crf 16 -preset slow` | High-quality x264 settings. Adjust for your delivery spec |
| `-color_range tv` | Label the output limited, matching the new pixels |

## 5. chromaverity's own CLI

```
chromaverity inspect FILE [--frames N] [--no-essence] [--json] [--out report.json] [--fail-on error|warn|info|never]
chromaverity diff BEFORE AFTER [--json] [--out report.json] [--fail-on ...]
chromaverity mcp [--root DIR]
```

| Exit code | Meaning |
|---|---|
| 0 | No findings at or above `--fail-on` (default `error`) |
| 1 | Findings at or above `--fail-on` |
| 3 | FFmpeg missing, failed, timed out, or no video stream |
| 4 | Input path refused (URL, directory, missing, outside `--root`) |

CI example: `chromaverity inspect out.mp4 --fail-on warn --out qc.json` fails the job on any warning and keeps the report as an artifact.
