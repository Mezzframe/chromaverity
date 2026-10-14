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

## Suggested order for the next few sprints

1. Run the zoo and read every evidence block in the reports. Explain CT301's confidence logic out loud.
2. Add one lint rule end to end (code, test, docs). Small, complete, teaches the whole loop.
3. Add a retag path for one more codec (AV1 via `av1_metadata` ⟨verify options⟩) with an end-to-end test that runs it.
4. Prototype the transfer check (CT31x) as a notebook before writing it as a module.
5. Start the v0.2 zoo with three public-domain clips.

## Where an AI pair helps most

- Explaining an FFmpeg filter's source code or docs line by line.
- Writing first-draft tests from a rule you describe in plain English.
- Spine checks on a change before you open a PR.

Where it helps least: deciding thresholds. Those come from measurement and broadcast experience, and they need a person who can say why.
