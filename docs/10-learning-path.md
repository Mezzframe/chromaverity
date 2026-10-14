# 10 · Learning path

What you need to work on chromaverity, in the order it pays off, and what's fine to hand to someone (or something) else.

## Skills map

| Skill | Where it shows up | Learn or outsource | Notes |
|---|---|---|---|
| Color science basics (range, matrix, transfer) | Everywhere | **Learn** | [01](01-color-primer.md), then BT.709 and H.273 themselves. This is the domain edge; it's what makes the tool credible |
| Reading FFmpeg commands | probe, essence, fixes | **Learn** | [04](04-cli-anatomy.md). Read the filter docs for every filter you touch |
| Python: dataclasses, type hints, pathlib, subprocess | All modules | **Learn** | Each module is short and commented on purpose. Read `tags.py`, then `safety.py`, then `range_check.py` |
| pytest | tests/ | **Learn** | Start by reading `test_range_classifier.py`: each test is one rule in plain English |
| Packaging (pyproject, extras, entry points) | pyproject.toml | Learn the basics | Comments in the file walk through it |
| Threat modeling | docs/07 | **Learn** | The STRIDE table there is a template for every future tool |
| CI (GitHub Actions) | .github/workflows | Learn the basics, outsource tuning | The workflow is ~100 lines, mostly comments. It runs on Linux, macOS and Windows |
| Shells on three systems (bash/zsh, PowerShell) | docs, CI, `fixes.py` | Learn the basics | Enough to activate a venv, quote a path with spaces, and read a CI log on each. [install.md](install.md) is the cheat sheet |
| MCP protocol details | mcp_server.py | Outsource the protocol, learn the pattern | Use the SDK; understand tools, roots and why the server is read-only |
| ML classifier training (v0.3) | essence/ | Learn the evaluation side, outsource heavy training | You need to judge a confusion matrix and spot leakage; you don't need to write a training loop from scratch |
| Signal processing depth (histograms, statistics) | essence/ | Learn as needed | Grows with each new check |

## A learning sequence: read, run, change

Each step has something to read, something to run, and something small to change. Do them in order; each one leans on the last.

1. **Read** [01](01-color-primer.md) up to "The four flags". **Run** `ffprobe -v error -select_streams v:0 -show_streams samples/good_limited_709.mp4` and find those four flags in the output. **Change** nothing yet.
2. **Read** [03](03-range-detection.md) "Method". **Run** `chromaverity inspect samples/full_pixels_labelled_limited.mp4 --json` and match every number in `evidence` to a line in the Rules block. **Change** `--frames 2` and see which evidence numbers move.
3. **Read** `tests/test_range_classifier.py`: each test is one rule in plain English. **Run** `pytest tests/test_range_classifier.py -v`. **Change** one threshold in `range_check.py` and watch which test tells you exactly which promise you broke. Put it back.
4. **Read** `tags.py`, then `lint.py`. **Run** `pytest -m "not ffmpeg"` (no FFmpeg needed). **Change**: add a lint rule end to end, following "Where to add things" in [02](02-how-it-works.md): code, test, a row in [06](06-checks-reference.md), a CHANGELOG line.
5. **Read** `safety.py` and [07](07-security.md) together. **Run** `chromaverity inspect http://example.com/x.mp4` and `echo $?` (`$LASTEXITCODE` in PowerShell) to see exit 4. **Change**: write one more test in `tests/test_safety.py` for a path you think should be refused.
6. **Read** [04](04-cli-anatomy.md) §3 and `fixes.py`. **Run** a proposed retag on a zoo clip, then `chromaverity diff` the before and after. **Change**: add a retag path for one more codec (AV1 via `av1_metadata` ⟨verify options⟩) with an end-to-end test that runs it.
7. **Read** [09](09-mislabel-zoo.md). **Run** `python scripts/make_zoo.py samples --list`. **Change**: add one zoo case for a mislabel we don't cover yet.

After that you're a maintainer. The sprint-sized items (prototype CT31x, start the v0.2 zoo) are in [ROADMAP.md](../ROADMAP.md).

## Where an AI pair helps most

Explaining an FFmpeg filter's source or docs line by line, and drafting tests from a rule you state in plain English. Where it helps least: deciding thresholds. Those come from measurement and broadcast experience, and they need a person who can say why.
