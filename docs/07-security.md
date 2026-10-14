# 07 · Security and threat model

**Depth:** standard (a published tool that reads untrusted files and can be driven by AI agents). Reviewed 2026-10-13.

## What chromaverity can and can't touch

| Can | Can't |
|---|---|
| Read files you point it at (CLI) or files under `--root` (MCP) | Write, move or delete any file |
| Start `ffprobe` and `ffmpeg` as child processes | Start anything else, or use a shell |
| Print commands for a person to run | Run those commands |
| | Open network connections (no code path does; FFmpeg is restricted to `file:`) |

## Trust boundaries

```
  person ──(CLI args)──┐
                       ├──► safety.py gate ──► ffprobe/ffmpeg (C parsers) ──► numbers ──► report
  agent ──(MCP call)───┘        │                     ▲                                     │
                                │                     │                                     ▼
                     refuses: URLs, protocols,   untrusted media file              agent / person
                     dirs, missing files,        (could be malformed or            (tags in the report
                     paths outside --root        crafted on purpose)                are untrusted data)
```

## Threats (STRIDE-style)

| # | Threat | Example | Control | Status |
|---|---|---|---|---|
| T1 | Command injection | Filename `a.mp4; rm -rf ~` | Subprocess with a list of args, never `shell=True`. Ruff `S` rules in CI | done, tested |
| T2 | Protocol abuse via "filename" | `http://attacker/x`, `concat:/etc/passwd\|...`, HLS playlist pointing at internal URLs | Reject protocol-looking paths; prefix `file:`; `-protocol_whitelist file` | done, tested |
| T3 | Path escape from MCP | Agent asks for `/etc/passwd` or `../../secret.mp4` | `--root` allow-list on resolved paths | done, tested |
| T4 | Parser crash or hang (DoS) | Malformed file triggers an FFmpeg bug or infinite loop | Timeout on every call (`CHROMAVERITY_TIMEOUT`, default 120 s); frames capped (MCP max 240) | done |
| T5 | FFmpeg memory-safety bug | Crafted file exploits a decoder | Out of our control. Keep FFmpeg patched; run untrusted batches in a container or VM | **document only** ⟨should⟩ |
| T6 | Prompt injection through metadata | A file's title/comment says "ignore previous instructions and run ..." | We only copy color fields, not free-text tags; reports carry an untrusted-data note; MCP is read-only | done ⟨should: add a test with a crafted tag once we read any free-text field⟩ |
| T7 | Agent runs a fix without consent | Agent pipes `command_text` into a shell | No apply path exists; MCP instructions say ask first; commands use `-n` (no overwrite) | done |
| T8 | Supply chain | Malicious dependency | Zero runtime deps; `mcp` optional and version-bounded; CI runs gitleaks and ruff | partial ⟨should: pin dev deps, Dependabot, SBOM at first release⟩ |
| T9 | Secret leak in repo | API key committed | `.gitignore` for `.env`; gitleaks pre-commit hook and CI job | done |
| T10 | Information disclosure in reports | Report contains absolute paths | Expected for a local tool; be aware before sharing reports publicly | accepted |

## Data handling

- chromaverity sends nothing anywhere. No telemetry.
- Reports contain file paths and color metadata only, never pixels.
- Test media is synthetic (FFmpeg test sources). Don't commit real footage you don't have rights to, and never commit employer material.

## Running untrusted files safely (recommended)

For files from strangers (issue attachments, scraped media), run inside a throwaway container with no network:

```bash
docker run --rm --network none -v "$PWD/inbox:/data:ro" chromaverity:dev inspect /data/file.mp4
```

`--network none` removes the network, `:ro` mounts the folder read-only. ⟨should: publish a Dockerfile in v0.2⟩

## Reporting a vulnerability

See [SECURITY.md](../SECURITY.md).
