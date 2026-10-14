# Roadmap

Sized for a few hours a week. Two-week sprints (Mezzframe DELIVERY spine). Order can change; the backlog lives in GitHub issues once the repo is public.

## v0.1 · "range truth" (this release)
- [x] Label lint (CT1xx), hop diff (CT2xx)
- [x] Range check against pixels (CT30x) with confidence and evidence
- [x] Proposed retag/convert commands (H.264, HEVC), never applied
- [x] MCP server, read-only, folder-restricted
- [x] Synthetic mislabel zoo v0.1 + 36 tests
- [x] CI green on GitHub from a clean clone
- [ ] Tag `v0.1.0`, publish to PyPI ⟨verify name still free⟩

## v0.2 · "zoo goes real"
- [x] FFmpeg version in every report (reproducibility)
- [ ] Command lines in every report
- [ ] Drop Python 3.10 (EOL 2026-10-01, PEP 619); raise requires-python to >=3.11 and move the 22.04 CI job to 3.11
- [ ] Dockerfile for running untrusted files with `--network none`
- [ ] Zoo v0.2: public-domain footage, full matrix of mislabels, realistic hops
- [ ] Publish range-check accuracy, false-alarm and inconclusive rates
- [ ] Full luma histogram + chroma evidence for range
- [ ] Retag via `av1_metadata` ⟨verify options⟩
- [ ] Pin dev deps, Dependabot, SBOM on release
- [x] CI on macOS and Windows too, so [install.md](docs/install.md) can say "tested" for all three
- [ ] New check: container `colr` box and bitstream VUI disagree (found while fixing FFmpeg 9 retags; needs the next free CT1xx/CT2xx ID)
- [ ] Print proposed fixes quoted for the user's shell (PowerShell/cmd on Windows), not only bash

## v0.3 · "transfer and matrix"
- [ ] CT31x transfer: PQ/HLG vs SDR from code-value distribution
- [ ] CT32x matrix: BT.601 vs BT.709. First learned classifier, trained on the zoo. Published either way, including if it doesn't work
- [ ] Optional `[ml]` extra (NumPy) if needed (ADR first)

## Later / ideas
- `--apply` with dry run + confirm (needs its own ADR)
- Scene-aware frame sampling
- Batch mode and an HTML report for archives
- Chroma siting check (CT33x)
- GitHub Action wrapper: `uses: Novapakt/chromaverity-action`

## Content angles
- "Your file says BT.709. The pixels disagree." (short video, the same frame decoded both ways)
- "We made 1,000 broken videos on purpose" (zoo v0.2 launch thread)
- "Can AI tell BT.601 from BT.709?" (v0.3, publish even if the answer is no)
