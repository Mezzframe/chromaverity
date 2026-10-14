# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions follow [SemVer](https://semver.org/); before 1.0, minor versions may break things and will say so.

## [Unreleased]

### Fixed
- Retag fixes did nothing on FFmpeg 9: the bitstream filter changed the H.264 header, but the MP4 `colr` box kept the input's old values and ffprobe reported the old label. Proposed retag commands now also pass `-color_range` / `-color_primaries` / `-color_trc` / `-colorspace` so the container agrees. The zoo's `hop_dropped_tags` clip had the same problem and is fixed the same way.
- `test_safety`: shell-characters test no longer assumes POSIX paths.

### Changed
- Renamed from the working name `colortruth` to `chromaverity` before first release (colortruth.com is registered and X-Rite's ColorTRUE is a color-calibration app; too close). Finding IDs keep the `CT` prefix, read as "color tag".
- Mislabel zoo generator is now FFmpeg-version-proof: pixels are made with plain arithmetic (`lutyuv`), labels are written afterwards with `h264_metadata`. FFmpeg 4.4 silently undid `scale=out_range=pc`, which made the old "good full range" clip a real mislabel.

### Added
- CI now runs on macOS and Windows as well as Ubuntu.
- `docs/install.md`: setup on macOS, Windows (PowerShell, cmd, Git Bash, WSL2) and Linux (Debian/Ubuntu, Fedora, Arch), shell quoting differences, MCP paths per system, troubleshooting. README, CONTRIBUTING and docs 04/08 now show Windows commands alongside macOS/Linux.
- `chromaverity inspect`: label lint (CT101-CT109), range check against pixels (CT300-CT304), proposed fixes.
- `chromaverity diff`: label changes across a hop (CT201-CT202).
- `chromaverity mcp`: read-only MCP server with `chromaverity_inspect` and `chromaverity_diff`, limited to `--root`.
- JSON report, schema 0.1.
- `scripts/make_zoo.py`: synthetic mislabel zoo v0.1 (7 clips).
- Educational docs (00-10, glossary, 4 ADRs), CI, gitleaks pre-commit hook.
