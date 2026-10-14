# Security policy

## Supported versions
Only the latest release and `main` get fixes while we're pre-1.0.

## Reporting a vulnerability
Please **don't** open a public issue. Use GitHub's private vulnerability reporting ("Security" tab → "Report a vulnerability"). Include the version, the command or MCP call, and a minimal file or the steps to generate one.

We'll acknowledge within 7 days and aim to fix or explain within 30. This is a small volunteer lab, so thanks for your patience.

## Scope
In scope: anything that makes chromaverity read files outside what it was given, reach the network, run a command, write or delete files, or crash/hang without hitting its timeout.

Out of scope: bugs inside FFmpeg itself. Report those to the FFmpeg project; we'll add a mitigation here if we can.

Threat model: [docs/07-security.md](docs/07-security.md).
