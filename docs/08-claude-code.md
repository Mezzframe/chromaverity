# 08 · Working in Claude Code (and wiring up agents)

Two different things live here: **developing** chromaverity with Claude Code, and **using** chromaverity as a tool inside any MCP-capable agent.

## Part A · Developing with Claude Code

### First run

These are the macOS / Linux commands. On Windows, see [install.md](install.md) for the PowerShell and cmd versions; only the venv lines differ.

```bash
git clone https://github.com/Novapakt/chromaverity.git
cd chromaverity
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,mcp]"
git config core.hooksPath .githooks                   # turn on the secret-scan pre-commit hook
pytest                                                # the test suite, a few seconds with FFmpeg
claude                                                # start Claude Code in the repo
```

| Command | Type | Construction |
|---|---|---|
| `python3 -m venv .venv` | Python module run as a program (`-m`) | Creates an isolated environment in `.venv/` so this project's packages don't touch your system Python |
| `source .venv/bin/activate` | shell builtin + script | Runs the activate script *in your current shell* (that's what `source` does), putting `.venv/bin` first on `PATH`. Windows PowerShell: `.venv\Scripts\Activate.ps1` (Windows venvs use `Scripts\`, not `bin/`) |
| `pip install -e ".[dev,mcp]"` | pip, editable install | `-e` links the package to your working copy, so edits take effect without reinstalling. `.[dev,mcp]` means "this folder, plus the `dev` and `mcp` optional extras" from `pyproject.toml`. Quotes stop zsh from treating `[...]` as a filename pattern |
| `git config core.hooksPath .githooks` | git config, per-repo | Tells git to run hooks from the tracked `.githooks/` folder instead of the untracked `.git/hooks/` |

Claude Code reads [`CLAUDE.md`](../CLAUDE.md) at the repo root automatically. It holds the project rules: run tests before claiming done, keep measure/classify split, no apply paths, update docs with code.

### Good first prompts

- "Read docs/02-how-it-works.md and explain the module map back to me."
- "Add the check from ROADMAP for a container `colr` box that disagrees with the bitstream VUI. Pick the next free CT1xx/CT2xx ID and follow the 'Where to add things' table in 02."
- "Run the zoo and show me the evidence for each CT3xx verdict."
- "Do a spine check on this change."

## Part B · chromaverity as an MCP tool

### What the agent gets

| Tool | Input | Returns |
|---|---|---|
| `chromaverity_inspect` | `path`, optional `frames` (1-240) | Full inspect report (findings, evidence, proposed fixes as text) |
| `chromaverity_diff` | `before`, `after` | Diff report |

Both are read-only and refuse paths outside `--root`. A bare filename (`clip.mp4`) is taken relative to `--root`. Refusals come back as data, `{"error": "UnsafeInput", "message": "..."}`, so the agent can tell the person what happened.

### Add it to Claude Code

The repo ships a project-scoped [`.mcp.json`](../.mcp.json) that points the server at `./samples`. That folder is git-ignored, so run `python scripts/make_zoo.py samples` once first, and start `claude` from a terminal with the venv active. Claude Code asks you to approve project MCP servers the first time ⟨verify current behavior⟩. Or add it yourself:

```bash
claude mcp add chromaverity -- chromaverity mcp --root ~/Videos/qc-inbox    # ⟨verify syntax for your Claude Code version⟩
```

| Piece | Meaning |
|---|---|
| `claude mcp add` | Claude Code subcommand that registers an MCP server |
| `chromaverity` | The name the agent will see |
| `--` | Everything after this is the command to launch, not options for `claude` |
| `chromaverity mcp --root ...` | Start our server over stdio, limited to that folder |

`chromaverity` has to be on the `PATH` Claude Code sees, which usually means starting `claude` from a terminal where the venv is active. If Claude Code reports "Executable not found in $PATH: chromaverity", give the full path to `.venv/bin/chromaverity` (macOS / Linux) or `.venv\Scripts\chromaverity.exe` (Windows) instead. Examples in [install.md](install.md#7-the-mcp-server-on-each-system).

### The loop we're designing for

```
 person: "make a 720p web version of master.mov"
 agent:  runs ffmpeg ... web.mp4
 agent:  chromaverity_diff(master.mov, web.mp4)
           ─► CT201 color_primaries dropped, CT201 color_transfer dropped
 agent:  "The transcode dropped the BT.709 labels. Here's a retag command (no re-encode).
          Want me to run it?"
 person: "yes"
```

That's the pitch in one exchange: the agent checks its own work, and a person approves the fix.
