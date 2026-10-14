# chromaverity docs

These docs are written so that anyone on the project can explain what chromaverity does and why, to an engineer or to a stranger. If a doc can't help you explain something, that's a bug: [open an issue](https://github.com/Novapakt/chromaverity/issues) and say which doc.

## Reading paths

| You are... | Start here | Then |
|---|---|---|
| Just want to run it | [Install](install.md) (macOS, Windows, Linux) | [04 §5 the CLI and its exit codes](04-cli-anatomy.md#5-chromaveritys-own-cli), then [06](06-checks-reference.md) when you get a finding |
| New to all of it | [00 Why](00-why.md) | [01 Color primer](01-color-primer.md) → [02 How it works](02-how-it-works.md) → run the zoo ([install §4](install.md#4-try-it)) → [03 Range detection](03-range-detection.md) → [06 Checks](06-checks-reference.md) → [05 Report format](05-report-format.md). The [glossary](glossary.md) is there for every term you meet on the way |
| A broadcast / video engineer | [00 Why](00-why.md) | [03 Range detection](03-range-detection.md), [06 Checks reference](06-checks-reference.md) |
| An AI / agent builder | [00 Why](00-why.md) | [08 Using it from Claude Code](08-claude-code.md), [05 Report format](05-report-format.md) |
| A contributor | [02 How it works](02-how-it-works.md) | [CONTRIBUTING](../CONTRIBUTING.md), [ADRs](adr/), [10 Learning path](10-learning-path.md) |
| Reviewing security | [07 Security](07-security.md) | [SECURITY.md](../SECURITY.md) |

## All docs

| # | Doc | Answers |
|---|---|---|
| 00 | [Why](00-why.md) | What problem, why now, why it's an AI tool, what already exists |
| 01 | [Color primer](01-color-primer.md) | Primaries, transfer, matrix, range, chroma siting, explained from scratch |
| 02 | [How it works](02-how-it-works.md) | Architecture, the three layers, module map, data flow |
| 03 | [Range detection](03-range-detection.md) | The first pixel check: method, thresholds, where it fails |
| 04 | [CLI anatomy](04-cli-anatomy.md) | Every FFmpeg/ffprobe command we run, flag by flag |
| 05 | [Report format](05-report-format.md) | JSON fields, stability promise, how agents should read it |
| 06 | [Checks reference](06-checks-reference.md) | Every finding ID (CT101...), what triggers it, what to do |
| 07 | [Security](07-security.md) | Threat model, trust boundaries, what the tool can and can't touch |
| 08 | [Claude Code](08-claude-code.md) | Developing in Claude Code, and wiring the MCP server into agents |
| 09 | [Mislabel zoo](09-mislabel-zoo.md) | The synthetic test set today, and the dataset/benchmark plan |
| 10 | [Learning path](10-learning-path.md) | What to learn, what to outsource, in what order |
| | [Install](install.md) | Setup on macOS, Windows and Linux, shell differences, troubleshooting |
| | [Glossary](glossary.md) | Terms, in one place |
| | [ADRs](adr/) | Decisions and the reasons behind them |
| | [Work orders](work-orders/) | Numbered maintenance tasks (WO-001, ...), each one a checklist Claude Code carried out and Mark reviewed commit by commit. Read one to see how changes get made here |

## Conventions used in these docs

- ⟨assumption⟩ marks something we believe but haven't measured.
- ⟨verify⟩ marks a fact that changes over time (versions, flags, defaults). Check it before relying on it.
- ⟨should⟩ marks a known gap we intend to close; ⟨PRO⟩ marks a question for a professional (lawyer, accountant) before it can be settled.
- Code values are 8-bit unless stated. Multiply by 4 for 10-bit, 16 for 12-bit.
- "Label" and "tags" mean the color metadata. "Essence" and "pixels" mean the picture itself. These are broadcast terms on purpose: metadata vs. essence is the distinction this whole tool is about.

Docs are licensed CC BY 4.0 (see [LICENSE-docs](../LICENSE-docs)). Code is Apache-2.0.
