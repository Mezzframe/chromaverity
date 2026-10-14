# WO-002 · Repo health sweep

> Status: done in #7

> Work order for Claude Code. Written 2026-10-14 from three read-only audits (code, docs, repo health) of `main` at `8392d57`, after WO-001 merged.
> Owner: Mark · Implementer: Claude Code · Spine depth: standard

## Read this first (for Claude Code)

The audits found the tests, git history and licensing clean, every finding ID in docs/06 matching the code, and no broken links. What needed work: one security gap, several real bugs, CI that couldn't tell when the FFmpeg suite skipped, thin test coverage on `fixes.propose` and `safety.run`, and docs that had drifted from the code.

**Rules** are those of WO-001: one branch (`chore/health-sweep`, from `main` after #6 merged), one commit per area (H1, H2, ...), explain every command, never push to `main`, never change GitHub settings, never invent names, emails or versions, stop at every ⏸ checkpoint.

## Decisions (Mark, 2026-10-14)

| # | Question | Decision |
|---|---|---|
| D1 | Start from the open release-prep branch or wait for #6? | Merge #6 first, branch from `main` |
| D2 | The sampler only reads the first 24 s but the docs say "the whole clip". Fix code or docs? | Fix the code: spread frames across the clip |
| D3 | Docs: accuracy only, or legibility too? | Both |
| D4 | docs/07 shows a Docker image that doesn't exist. Build it now? | No; mark the section planned, Dockerfile stays in v0.2 |

## Tasks

### H1 · Security
⏸ Checkpoint: show the repro before committing.
- Nested-reference escape from `--root`: a playlist under root lists a file outside it; `-protocol_whitelist file` allows it. Repro first, then `-format_whitelist` on both FFmpeg calls via one shared `INPUT_GUARDS`. Keep the repro as a test.
- `safety.run()`: `encoding="utf-8", errors="replace"`, `stdin=DEVNULL`, drop the unused `binary` parameter.
- `report.inspect/diff` gate their own inputs. `report.plain()` strips control characters from text output and error messages.
- Tests: `run()` timeout, exit tail, UTF-8; symlink escape; sibling-prefix root; `~`; the repro.

### H2 · Bugs
- Bit depth from pixel-format names (`p010le`, `gray10le`, `v210`...), tested against `ffmpeg -pix_fmts`.
- No BT.709 fill when a set field says BT.2020/PQ/HLG. Convert fix with the note for codecs without a retag path, on every branch. `looks_full` from evidence, not the title.
- Sampling: `fps = frames / duration` (D2); `sample_fps` in evidence; a 40 s black-leader test clip.
- CLI: exit 3 for `OSError`, exit 4 for `--out` over an input, exit 2 documented; `CHROMAVERITY_TIMEOUT` validated.
- MCP: relative paths against `--root`; missing extra is a `ToolError`.
- Tests: new `tests/test_fixes.py`; lint negatives; diff paths; exit codes; MCP relative paths.

### H3 · Dead code
Remove `from_tags_only`; fix the `tests/test_lint.py` pointer; readable HDR cell; document `notes` as reserved.

### H4 · CI and tooling
Build job (`python -m build`, `twine check`); `timeout-minutes`; concurrency; pip cache; `CHROMAVERITY_REQUIRE_FFMPEG=1` turns the skip into a failure; Windows steps run install.md's lines as written. pyproject: dynamic version, classifiers, `py.typed`, `mcp>=2.3,<3`, `build`/`twine` in dev, ruff RUF/SIM/C4/PTH, pytest `-ra --strict-markers`. Hook: `gitleaks git --pre-commit --staged`. `.gitignore` additions. Issue-template `config.yml`.

### H5 · Docs accuracy
Everything that contradicted the code: test counts, done items listed as pending, exit code table, who starts processes, docs/06 "fires when" wording, CT304's one-band rule, the measured table (all 7 clips, FFmpeg 9.0.2), the README sample, docs/05's full field list and MCP refusal shape, the docs/08 starter prompt.

### H6 · Docs legibility
Glossary for every undefined term; README ends on "Where next"; beginner reading path; seven-step learning sequence; lead-ins before dense blocks; "What to do with a finding"; "Untested so far"; Docker section planned (D4); update/uninstall; voice fixes.

### H7 · CHANGELOG, this file, PR
One PR, spine table, `gh label create` commands and open items listed for Mark.

## Acceptance

```bash
ruff check .
pytest                                   # 111 passed; 1 pwsh skip off Windows
python -m build && twine check dist/*
chromaverity inspect samples/good_limited_709.mp4 --out samples/good_limited_709.mp4; echo $?   # 4, file untouched
```

…and CI green on all six jobs, including `build`.

## Out of scope (next work order)

- Tag and publish v0.1.0 (needs the Code of Conduct contact and the ⟨PRO⟩ copyright answer first).
- T11: planted `ffmpeg.exe` in the current folder on Windows.
- Dockerfile (D4), command lines in reports, cmd.exe quoting.
