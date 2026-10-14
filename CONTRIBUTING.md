# Contributing

Thanks for looking. chromaverity is part of the Mezzframe AI open lab, and we write everything with a stranger in mind, so you're exactly who this is for.

## Ways to help
| Effort | Idea |
|---|---|
| 5 minutes | Fix a typo or an unclear sentence in the docs |
| An hour | Report a real file chromaverity got wrong (ffprobe output + report JSON, no footage you can't share) |
| An evening | Add a lint rule or a retag path for another codec |
| A project | A new pixel check (transfer, matrix), or zoo v0.2 |

## Setup
Per-system install steps (macOS, Windows, Linux) are in [docs/install.md](docs/install.md). Working with Claude Code: [docs/08-claude-code.md](docs/08-claude-code.md), Part A. Short version:

macOS / Linux:
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,mcp]"
git config core.hooksPath .githooks
pytest && ruff check .
```

Windows PowerShell:
```powershell
python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -e ".[dev,mcp]"
git config core.hooksPath .githooks
pytest; ruff check .
```

Any of macOS, Windows or Linux is fine to contribute from; CI tests all three.

## Pull requests
1. One change per PR. Small is good.
2. Tests for new behavior. Pixel checks need a pure classifier test **and** a zoo case.
3. Update the docs in the same PR (checks reference, how-it-works, CHANGELOG `[Unreleased]`).
4. Fill in the PR template, including a lite spine check.
5. Never commit media you don't have rights to, or anything from an employer.

## Writing docs for three systems
Contributors use macOS, Windows and Linux, so every command in the docs has to work for all of them.
- If a command is the same everywhere (`pytest`, `chromaverity inspect ...`, `git ...`), one `bash` block is fine. Say so if it's not obvious.
- If it differs (installing tools, activating the venv, `head`, `$PWD`, `\` line breaks), give a macOS/Linux block **and** a Windows PowerShell block. Add cmd only where people really use it.
- Put the details in [docs/install.md](docs/install.md) and link to it rather than repeating them.
- Mark anything you couldn't test on a system with ⟨assumption⟩.

## Ground rules from the codebase
Read [CLAUDE.md](CLAUDE.md) "Rules of the codebase". The big ones: no shell, no apply paths, measure/classify split, stable finding IDs.

## Licensing of contributions
By contributing you agree your code is licensed Apache-2.0 and your docs CC BY 4.0, as described in the license files (Apache-2.0 §5 covers code contributions).

## Conduct
See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
