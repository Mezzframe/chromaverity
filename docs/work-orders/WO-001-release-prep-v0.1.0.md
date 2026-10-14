# WO-001 · Release prep for v0.1.0

> Status: done in #6

> Work order for Claude Code. Written 2026-10-14 from a health check of `main` at `0bd05e7`.
> Owner: Mark · Implementer: Claude Code · Spine depth: standard (published tool)

## Read this first (for Claude Code)

You're picking up a repo health check. The code is in good shape: lint is clean, 40 tests pass, 1 is skipped (PowerShell, expected off Windows), and CI is green on Ubuntu, macOS and Windows. This work order closes the gaps between "works" and "ready to tag v0.1.0".

**Rules for this work order**

1. Read `CLAUDE.md` first. Its codebase rules apply here.
2. Work on one branch, `chore/release-prep-v0.1.0`, with **one commit per task** (T1, T2, ...) so Mark can review them one at a time. Open one PR at the end. Never push to `main`.
3. **Don't change GitHub repo settings.** Settings, About fields and branch protection are Mark's, listed under "Mark does these" below. You may print the commands for him.
4. **Don't invent anything.** No email addresses, no legal names, no version numbers from memory. Look versions up with the commands given. If a lookup fails, stop and say so.
5. Explain as you go. Mark is learning. For every command you run, say what it is and how it's built.
6. Stop and ask Mark at each **⏸ checkpoint**.

## Decisions (Mark fills in before starting; defaults shown)

| # | Question | Default if left blank |
|---|---|---|
| D1 | Python 3.10 reaches end of life in October 2026 ⟨verify: PEP 619⟩. Support it in v0.1.0? | **Keep 3.10 for v0.1.0.** Add a ROADMAP item to drop it in v0.2 |
| D2 | Contact for Code of Conduct reports | **Leave the placeholder.** Don't invent an address |
| D3 | Legal author / copyright holder for `NOTICE` and `CITATION.cff` | **Leave as is.** `[PRO]` item, waiting on an attorney |

## Tasks

### T1 · Dependabot for actions and pip

**Why:** the Node 20 warnings happened because nothing told us the actions were going stale. Dependabot opens a PR when a new version ships, and it keeps SHA pins (T2) current.

**Do:** create `.github/dependabot.yml`:

```yaml
# Dependabot: opens PRs when our dependencies have new versions.
# Each PR runs the full CI, so an update only merges if tests still pass.
version: 2
updates:
  - package-ecosystem: "github-actions"   # the uses: lines in .github/workflows/
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      actions:                             # one PR for all action bumps, not one per action
        patterns: ["*"]
  - package-ecosystem: "pip"               # optional extras in pyproject.toml (mcp, dev)
    directory: "/"
    schedule:
      interval: "weekly"
```

**Done when:** the file exists, and `python -c "import yaml,sys; yaml.safe_load(open('.github/dependabot.yml'))"` runs without error (install PyYAML into `.venv` temporarily if needed, and don't add it to `pyproject.toml`).

### T2 · Pin GitHub Actions to commit SHAs

**Why (SEC spine, should):** a tag like `v6` can be moved to different code by whoever controls the action's repo. A full commit SHA can't. The version comment keeps it readable, and Dependabot updates both.

**Do:** for each `uses:` line in `.github/workflows/ci.yml` (`actions/checkout`, `actions/setup-python`, `gitleaks/gitleaks-action`):

1. Find the newest release **within the current major** (`v6`, `v6`, `v3`):
   ```bash
   gh release list -R actions/checkout --limit 5
   ```
2. Get the commit SHA that release points to:
   ```bash
   gh api repos/actions/checkout/commits/v6.0.3 --jq .sha     # use the tag from step 1
   ```
   (`commits/<tag>` returns the commit itself, even for annotated tags. `git/ref/tags/<tag>` can return a tag object's SHA instead, which is the wrong thing to pin.)
3. Replace the line, keeping the version as a comment:
   ```yaml
   - uses: actions/checkout@<40-char-sha>  # v6.0.3
   ```

Also delete the now-stale header comment line `# ⟨verify⟩ action major versions before first run; SEC spine "should": pin actions by commit SHA.` and replace it with `# Actions are pinned to commit SHAs (version in the comment); Dependabot keeps them current.`

**Done when:** `grep -n "uses:" .github/workflows/ci.yml` shows only 40-character SHAs, each followed by a `# vX.Y.Z` comment. CI passes on the PR.

⏸ **Checkpoint:** show Mark the three SHAs and their versions before committing.

### T3 · Fill the `<org>` placeholders

**Why:** the repo now exists at `github.com/Novapakt/chromaverity`, and PyPI, citation tools and readers use these URLs.

**Do:**

| File | Change |
|---|---|
| `pyproject.toml` `[project.urls]` | Uncomment and fill: `Repository = "https://github.com/Novapakt/chromaverity"`. Add `Issues = "https://github.com/Novapakt/chromaverity/issues"` and `Changelog = "https://github.com/Novapakt/chromaverity/blob/main/CHANGELOG.md"`. Keep `Homepage` |
| `CITATION.cff` | Uncomment `repository-code: "https://github.com/Novapakt/chromaverity"`. **Leave the author line and its `[PRO]` comment alone** (D3) |
| `ROADMAP.md` | `uses: <org>/chromaverity-action` → `uses: Novapakt/chromaverity-action` |

Don't touch `CODE_OF_CONDUCT.md` unless D2 has an answer.

**Done when:** `grep -rn "<org>" --exclude-dir=.git .` prints nothing, and `pip install -e .` still works.

### T4 · Record the FFmpeg version in every report

**Why (CLOUD/ML spine, should):** the 4.4 and 9.0 bugs both came down to FFmpeg version. A report that doesn't say which FFmpeg produced it can't be reproduced or compared. This is the most useful field we don't have yet.

**Do:**

1. In `src/chromaverity/report.py`, add an `ffmpeg` object to `_envelope()`:
   ```jsonc
   "ffmpeg": {"version": "6.1.1-3ubuntu5"}   // null if it can't be read
   ```
2. Get it from the first line of `ffmpeg -version` (`ffmpeg version 6.1.1-3ubuntu5 Copyright ...` → the third word). Rules:
   - run it through `safety.run()` with `require_binary("ffmpeg")`, same as every other call (CLAUDE.md rule 1);
   - cache it with `functools.lru_cache`, so one process asks once;
   - on any `ToolError`, or output that doesn't start with `ffmpeg version`, return `None`. Never fail the report over this.
3. Put the parsing in a small pure function (`parse_ffmpeg_version(first_line: str) -> str | None`) so it can be tested without FFmpeg (ADR 0003 spirit).
4. Tests in `tests/test_tags_lint_diff.py` or a new `tests/test_report_envelope.py`:
   - parse: `"ffmpeg version 6.1.1-3ubuntu5 Copyright (c) 2000-2023"` → `"6.1.1-3ubuntu5"`; `"ffmpeg version n7.1 Copyright"` → `"n7.1"`; `"garbage"` → `None`;
   - end to end (marked `ffmpeg`): an inspect report has `report["ffmpeg"]["version"]` as a non-empty string.
5. Text output: add the version to the header line, e.g. `chromaverity 0.1.0.dev0 · FFmpeg 6.1.1 · /path/clip.mp4`.
6. Docs: add the field to the shape in `docs/05-report-format.md`. It's a new field, so **no schema version bump** (see that doc's stability table). Regenerate `examples/inspect-full-labelled-limited.json` with `python scripts/make_zoo.py samples` and `chromaverity inspect samples/full_pixels_labelled_limited.mp4 --frames 4 --json`, then replace the absolute `samples/` path prefix with `zoo/` the same way the existing example does.
7. In `docs/03-range-detection.md` and `docs/09-mislabel-zoo.md`, nothing changes, but the "What this does not show" section in 03 can now say results are tagged with the FFmpeg version.

**Done when:** all tests pass, including the new ones; `--json` output includes `ffmpeg.version`; ruff is clean.

### T5 · Small docs fixes

| File | Change | Why |
|---|---|---|
| `docs/09-mislabel-zoo.md` | "Three lessons found while building it, **both** exactly..." → "Three lessons found while building it, **all** exactly..." | Grammar left over from when there were two |
| `ROADMAP.md` v0.2 | Tick or remove "Record FFmpeg version and command lines in every report" → split into `[x] FFmpeg version in every report` (done in T4) and `[ ] command lines in every report` | Keep the roadmap honest |
| `ROADMAP.md` v0.2 | If D1 = default, add `[ ] Drop Python 3.10 (EOL October 2026 ⟨verify⟩); raise requires-python to >=3.11 and move the 22.04 CI job to 3.11` | |
| `ROADMAP.md` v0.1 | Tick `[x] CI green on GitHub from a clean clone` | Measured 2026-10-14 |

**Don't** touch the `⟨enable this in repo settings⟩` note in `SECURITY.md`. It comes out only after Mark confirms M2 below (see T6).

### T6 · SECURITY.md note (only after Mark confirms M2)

⏸ **Checkpoint:** ask Mark: "Is private vulnerability reporting turned on?" If yes, remove ` ⟨enable this in repo settings⟩` from `SECURITY.md`. If no or unsure, skip this task and list it as open in the PR description.

### T7 · CHANGELOG

Under `## [Unreleased]`, add:

- **Added:** `ffmpeg.version` in every report and in the text header (T4); Dependabot for actions and pip (T1).
- **Changed:** GitHub Actions pinned to commit SHAs (T2); project URLs filled in (T3).

### T8 · Open the PR

- Title: `chore: release prep for v0.1.0 (WO-001)`
- Body: one line per task with its commit, the decisions used (D1-D3), and a **spine check** table (the PR template asks for one; PRs #1-#5 skipped it):

| Spine | Finding | Decision |
|---|---|---|
| NET | n/a: no network code touched | n/a |
| SEC | Actions SHA-pinned; Dependabot on; vuln reporting (M2) | ... |
| CLOUD/ML | FFmpeg version now recorded in reports | ... |
| DELIVERY | Closes WO-001; v0.1.0 tag is the next step | ... |

- This file lives at `docs/work-orders/WO-001-release-prep-v0.1.0.md`. As the last commit, add `> Status: done in #<PR number>` under the title and include it in the PR, so the next work order has a pattern to follow.

## Mark does these (GitHub settings; Claude Code doesn't)

| # | What | How |
|---|---|---|
| M1 | About: description, website, topics | `gh repo edit Novapakt/chromaverity --description "Check whether a video's color labels match its pixels." --homepage "https://mezzframe.ai" --add-topic video,ffmpeg,color,broadcast,qc,hdr,mcp` |
| M2 | Private vulnerability reporting | Repo → Settings → Advanced Security (or "Code security") → Private vulnerability reporting → Enable ⟨verify menu name⟩ |
| M3 | Dependabot alerts and security updates | Same page → Dependabot alerts → Enable; Dependabot security updates → Enable |
| M4 | Protect `main` | Settings → Branches (or Rules → Rulesets) → add a rule for `main`: require a pull request, require status checks `test (ubuntu-22.04, 3.10)`, `test (ubuntu-24.04, 3.13)`, `test (macos-latest, 3.13)`, `test (windows-latest, 3.13)`, `secrets`; block force pushes |

`gh repo edit` explained: `gh` is the GitHub CLI, `repo edit` changes repository settings, `OWNER/REPO` says which repo, each `--flag "value"` sets one field, and `--add-topic` takes a comma-separated list.

Do M4 **after** this PR merges. Otherwise the new rule will want checks the branch hasn't run yet.

## Acceptance (whole work order)

```bash
git switch chore/release-prep-v0.1.0
ruff check .
pytest                                   # all pass; 1 skip off Windows is expected
grep -rn "<org>" --exclude-dir=.git .    # prints nothing
grep -n "uses:" .github/workflows/ci.yml # SHAs with version comments
chromaverity inspect samples/good_limited_709.mp4 --json | python -c "import json,sys; print(json.load(sys.stdin)['ffmpeg'])"
```

…and CI is green on the PR across all five jobs.

## Out of scope (next work order)

- Tagging and publishing `v0.1.0` (GitHub release, PyPI ⟨verify name still free⟩).
- Command lines in reports.
- Dockerfile for running untrusted files with `--network none`.
- Anything needing a `[PRO]` answer (D3, trademark clearance, patent read before the v0.3 classifier).
