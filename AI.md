# How we use AI in chromaverity

Short version: **AI helps write this tool; a person decides what goes in.** Every change was reviewed, tested and merged by the maintainer. This page says exactly where AI is involved, so you can judge the work for yourself.

## 1. AI that helped build chromaverity

| Part | How AI was used | What a person did |
|---|---|---|
| Code and tests | Written with Claude Code (Anthropic's coding agent) from work orders the maintainer wrote and approved. The work orders are in [`docs/work-orders/`](docs/work-orders/) | Read every diff, ran the tests, asked for changes, merged |
| Docs | Drafted with Claude, in the same changes as the code | Edited for accuracy and voice |
| Test results | The checks were run on real footage by the maintainer; Claude helped read the output | Separated what was measured from what was assumed (marked ⟨assumption⟩ and ⟨verify⟩ in the docs) |

How to see it in the history: from PR #1 onward, commits written with AI help carry a `Co-Authored-By: Claude …` trailer. The first upload (`a91738a` and the commits before it) was also written with Claude, in a chat session, and has no trailer. Run `git log --format='%h %an %(trailers:key=Co-Authored-By,valueonly,separator=%x2C )'` to list them.

| Part of that command | What it does |
|---|---|
| `git log` | Shows the commit history |
| `--format='…'` | Prints each commit in a custom layout instead of the default |
| `%h` and `%an` | Short commit hash and author name |
| `%(trailers:key=Co-Authored-By,valueonly,…)` | The value of any `Co-Authored-By:` line at the end of the commit message |

Rules the AI works under are in [`CLAUDE.md`](CLAUDE.md): run the tests before saying something is done, never touch media files, no shell commands from the code, and treat file contents as data, not instructions.

## 2. AI that uses chromaverity

chromaverity also runs as an MCP server, so AI agents can call it to check their own transcodes ([setup](docs/08-claude-code.md), Part B). By design:

- Agents get two **read-only** tools, limited to one folder.
- Fixes come back as **text** for a person to read and run. No code path changes, moves or deletes media ([ADR 0004](docs/adr/0004-propose-never-apply.md)).
- Filenames and metadata in a video are treated as data, so a crafted file can't instruct the agent through chromaverity's output.

## 3. What AI does not do here

- Merge changes, publish releases or change repo settings. Those stay with the maintainer.
- Decide what a check reports. Verdicts come from measured pixel statistics and fixed rules ([how it works](docs/02-how-it-works.md), [ADR 0002](docs/adr/0002-deterministic-before-ai.md)), not from a model's judgement.
- Run on your files when you use the CLI. chromaverity itself has no AI in it.

## 4. Questions or problems

If something here looks wrong, or you think AI-written code caused a bug, open an issue. Security problems go through [`SECURITY.md`](SECURITY.md).

This page is part of how the [Mezzframe](https://mezzframe.ai) lab works: AI proposes, people approve.
