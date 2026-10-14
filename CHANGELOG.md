# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions follow [SemVer](https://semver.org/); before 1.0, minor versions may break things and will say so.

## [Unreleased]

## [0.1.0] - 2026-10-14

First release. Everything below is new in 0.1.0; the Security, Fixed, Changed and Removed sections describe changes made during the pre-release hardening (WO-001, WO-002), kept so the history of each decision is readable.

### Security
- A playlist file (`.m3u8`) saved under the MCP `--root` could make ffprobe read files outside that folder: `-protocol_whitelist file` still lets FFmpeg follow `file:` entries inside the input (measured on FFmpeg 9.0.2). Both FFmpeg calls now also pass `-format_whitelist` with the containers we read; playlist demuxers (HLS, DASH, concat) are not on it. Files in other containers (raw `.h264`, `.y4m`, images) are refused with exit 3 where they used to be read.
- Text output and error messages replace terminal control characters in filenames and commands with `?` (`report.plain()`), so a crafted filename can't rewrite the window title or hide text. JSON output was already escaped.
- `report.inspect()` and `report.diff()` run their inputs through the same path gate as the CLI and MCP server, so library callers get the same refusals.
- Child processes get `stdin=/dev/null`; in MCP mode they can no longer inherit the protocol pipe.

### Fixed
- Bit depth was read as 8 for `p010le`, `p016le`, `gray10le`, `gray12le`, `v210`, `x2rgb10le` and other formats whose name doesn't contain `p10`-style text, which scaled the range thresholds wrong and could produce a false CT301. New `bit_depth_from_pix_fmt()` with a table for the odd names, tested against `ffmpeg -pix_fmts`.
- The CT101 "fill blanks with BT.709" fix was offered when a set field already said BT.2020 (it wrote a 709 matrix under 2020 primaries) or when transfer was blank on HDR content. It's now skipped when any set field says BT.2020, PQ or HLG.
- The range check sampled only the first 24 seconds (`fps=1`, 24 frames), so a clip with a black or bars leader got a verdict from the leader alone. Frames are now spread across the clip (`fps = frames / duration`); the rate used is in `evidence.sample_fps`. Measured: a 40 s clip with a 30 s black leader and a full-range body went from CT304 "agrees" to CT301.
- On Windows, FFmpeg output was decoded with the console code page instead of UTF-8, so a non-ASCII stream title could raise `UnicodeDecodeError` mid-report (exit 1, which looks like "findings").
- Crashes exited 1, the same code as "findings found". `--out` to an unwritable path now exits 3; `--out` pointing at one of the inputs is refused with exit 4 instead of overwriting the media; exit 2 (bad arguments) is documented.
- MCP: a bare filename (`clip.mp4`) resolved against the server's working directory, not `--root`, so the shipped `.mcp.json` refused every example. Relative paths are now relative to `--root`.
- MCP without the `[mcp]` extra raised `SystemExit` with a bare message; it's a normal exit 3 with the install hint now.
- A bad `CHROMAVERITY_TIMEOUT` value crashed at import; it now falls back to 120 s with a warning.
- Codecs with no lossless retag path (ProRes, AV1, ...) got no proposal at all for CT302/CT303-limited; they now get a convert fix with the explanation attached, as CT301 already did.
- `fix_hint` on CT201 no longer suggests a retag for pixel-format and bit-depth changes, which the finding itself calls deliberate.
- CI: the Windows FFmpeg install retries when Chocolatey's server times out, and fails clearly instead of reporting success with nothing installed.
- Text output could crash on Windows (`UnicodeEncodeError`) when piped or redirected, for any filename outside the console's code page (e.g. `クリップ.mp4`) and for the CT101 fix note. Unencodable characters now print as `?`; JSON and `--out` were never affected.
- Retag fixes did nothing on FFmpeg 9: the bitstream filter changed the H.264 header, but the MP4 `colr` box kept the input's old values and ffprobe reported the old label. Proposed retag commands now also pass `-color_range` / `-color_primaries` / `-color_trc` / `-colorspace` so the container agrees. The zoo's `hop_dropped_tags` clip had the same problem and is fixed the same way.
- `test_safety`: shell-characters test no longer assumes POSIX paths.

### Changed
- CI: a build job (`python -m build`, `twine check`, wheel listing); job timeouts; superseded runs are cancelled; pip cache; `CHROMAVERITY_REQUIRE_FFMPEG=1` makes a runner without FFmpeg fail instead of silently skipping the end-to-end suite; the Windows steps run the lines from `docs/install.md` as written.
- Packaging: version is read from `__init__.py` (one place to bump); classifiers for Python 3.10-3.13; `py.typed`; `mcp>=2.3,<3`; `build` and `twine` in the `dev` extra; explicit sdist contents.
- Lint: ruff rule sets `RUF`, `SIM`, `C4`, `PTH` added; pytest runs with `-ra --strict-markers`.
- Pre-commit hook uses `gitleaks git --pre-commit --staged` (the `protect` form is deprecated), with a fallback for older installs.
- Docs: glossary roughly doubled (every term the docs used without defining it); a beginner reading path and a seven-step learning sequence; "What to do with a finding" in the checks reference; measured table and README sample regenerated on FFmpeg 9.0.2; facts that had drifted from the code (test counts, exit codes, "fires when" wording, which modules start processes, done items listed as pending) corrected; the Docker section marked planned.
- The organization is now called "Mezzframe" everywhere (was "Mezzframe AI"): README, CONTRIBUTING, CLAUDE.md, package metadata, NOTICE, CITATION.cff, LICENSE-docs credit line. The domain stays mezzframe.ai.
- GitHub Actions in CI are pinned to commit SHAs, with the version in a comment (checkout v6.1.0, setup-python v6.3.0, gitleaks-action v3.0.0).
- Project URLs filled in: `pyproject.toml` (Repository, Issues, Changelog) and `CITATION.cff` (`repository-code`).
- Renamed from the working name `colortruth` to `chromaverity` before first release (colortruth.com is registered and X-Rite's ColorTRUE is a color-calibration app; too close). Finding IDs keep the `CT` prefix, read as "color tag".
- Mislabel zoo generator is now FFmpeg-version-proof: pixels are made with plain arithmetic (`lutyuv`), labels are written afterwards with `h264_metadata`. FFmpeg 4.4 silently undid `scale=out_range=pc`, which made the old "good full range" clip a real mislabel.

### Removed
- `report.from_tags_only()`: no callers and no documented library API.

### Added
- Release workflow (`.github/workflows/release.yml`): publishing a GitHub release builds the package, checks the tag matches the version, and uploads to PyPI with Trusted Publishing (no stored token). Steps in `docs/release.md`.
- `evidence.looks_full` and `evidence.sample_fps` on CT30x findings; `ffmpeg.version` documented as `{"version": null}` when unreadable. New fields, no schema bump.
- Tests: `tests/test_fixes.py` (pure tests for every proposed-fix path, including that no metadata string can reach a command); `safety.run()` timeout, exit-tail and UTF-8 cases; symlink and sibling-prefix root escapes; the playlist escape; bit depth per pixel format; the remaining lint rules and their negatives; CLI exit codes for `--out` and `--fail-on`; MCP relative paths; the black-leader clip. 111 tests, up from 44.
- `.github/ISSUE_TEMPLATE/config.yml` points security reports at the private form.
- `ffmpeg.version` in every report (null if FFmpeg can't be read), also shown in the text header. New report field, no schema bump.
- Dependabot for GitHub Actions and pip, checked weekly.
- Every proposed fix now has `command_text_powershell` next to `command_text` (bash). The text output shows the PowerShell form on Windows (`PS> ...`). New report field, no schema bump. Quoting is tested by round-tripping awkward filenames through real PowerShell.
- `.gitattributes` (LF line endings everywhere, so the bash pre-commit hook works on Windows) and `.editorconfig`.
- CI on Windows also follows docs/install.md in PowerShell and cmd.exe, not only Git Bash.
- CONTRIBUTING "Writing docs for three systems"; PR template checkbox; CLAUDE.md rule.
- CI now runs on macOS and Windows as well as Ubuntu.
- `docs/install.md`: setup on macOS, Windows (PowerShell, cmd, Git Bash, WSL2) and Linux (Debian/Ubuntu, Fedora, Arch), shell quoting differences, MCP paths per system, troubleshooting. README, CONTRIBUTING and docs 04/08 now show Windows commands alongside macOS/Linux.
- `chromaverity inspect`: label lint (CT101-CT109), range check against pixels (CT300-CT304), proposed fixes.
- `chromaverity diff`: label changes across a hop (CT201-CT202).
- `chromaverity mcp`: read-only MCP server with `chromaverity_inspect` and `chromaverity_diff`, limited to `--root`.
- JSON report, schema 0.1.
- `scripts/make_zoo.py`: synthetic mislabel zoo v0.1 (7 clips).
- Educational docs (00-10, glossary, 4 ADRs), CI, gitleaks pre-commit hook.

[Unreleased]: https://github.com/Novapakt/chromaverity/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Novapakt/chromaverity/releases/tag/v0.1.0
