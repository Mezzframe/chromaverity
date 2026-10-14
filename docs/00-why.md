# 00 · Why chromaverity exists

## The problem in one sentence

Every video file carries a color label, every tool trusts it, and nobody checks whether the label matches the picture.

## A story every video engineer has lived

A clip comes back from an edit, a cloud transcode or an AI upscaler. On the reference monitor it looks fine. On the website the blacks are grey and the whole thing looks washed out. On a phone the shadows are crushed. Someone spends an afternoon in forums working out that a flag called `color_range` says one thing and the pixels say another.

The pixels were never damaged. The **label** was wrong, and every player downstream did exactly what the label told it to.

## Label vs. pixels (metadata vs. essence)

Broadcast already has words for this. **Essence** is the picture and sound. **Metadata** describes the essence. In SDI and ST 2110 plants, the format is enforced: the router, the frame sync and the monitor all agree on 1080i59.94 BT.709 because the whole facility is timed and configured that way.

Files have no such plant. The label travels inside the file, written by whatever software touched it last. Any hop can drop it, rewrite it or guess it:

```
 camera ──► NLE export ──► cloud transcode ──► AI upscale ──► packager ──► player
   │           │                 │                  │              │          │
 label ok   label ok?        label dropped?     label reset?   label ok?   trusts
                                                                           whatever
                                                                           arrives
```

Broadcast analogy: a tally light that says "on air" while the router is feeding a different source. The light isn't broken. It's reporting what it was told.

## What already exists (and where the gap is)

| Tool | Reads the label | Checks the label against the pixels | Open |
|---|---|---|---|
| ffprobe, MediaInfo | yes | no | yes |
| MediaConch (policy checker) | yes, against rules you write | no | yes |
| Commercial file QC (e.g. Baton, Vidchecker, Pulsar) | yes | some essence checks ⟨verify per product⟩ | no |
| Forum threads | by hand | by hand, one file at a time | n/a |
| **chromaverity** | yes | **yes, with a confidence level and the numbers behind it** | yes |

The label-only checks are well covered, so chromaverity keeps them short. Its reason to exist is the second column: **does the picture agree with what the file says about itself?**

## Why this is an AI tool (and where the AI is not)

Two honest answers.

**1. It's built for AI agents to use.** Agents now write and run FFmpeg commands inside real pipelines. They get the syntax right and forget color flags all the time ⟨assumption, easy to demo⟩. chromaverity runs as an MCP server, so an agent can check its own work: transcode, call `chromaverity_diff`, see what it dropped, and ask the person before fixing it. Think of it as a QC probe on the agent's output bus.

**2. The pixel checks are designed to become learned models.** v0.1 uses hand-set thresholds (deterministic, explainable, testable). The harder checks, such as telling a BT.601 matrix from BT.709 from pixels alone, need a learned classifier. The training data for that doesn't exist in public, so we're building it: the [mislabel zoo](09-mislabel-zoo.md), where known-good pixels get deliberately wrong labels, giving unlimited ground truth for free.

Where the AI is **not**: the AI doesn't decide pass/fail on its own, and it never runs a fix. The tool measures and reports numbers; a model may explain or rank; a person approves any change. See [ADR 0002](adr/0002-deterministic-before-ai.md).

## Why it could matter to people outside broadcast

- **AI video builders** ship generated and upscaled video that is often untagged ⟨verify on current models⟩. chromaverity tells them what the pixels look like so they can label correctly.
- **Archivists** digitizing tape and film need labels they can trust for the next 50 years. A wrong range flag in an archival master is a slow-motion disaster (see the Preserve topic at mezzframe.ai).
- **Streaming engineers** get a cheap, open check to drop into CI before a ladder ships.

## What v0.1 does and doesn't do

| Does | Doesn't (yet) |
|---|---|
| Reads and lints the label (CT1xx) | Detect transfer (PQ vs SDR) from pixels |
| Diffs the label across one hop (CT2xx) | Detect matrix (601 vs 709) from pixels |
| Checks **range** against the pixels (CT3xx) | Check chroma siting |
| Proposes FFmpeg fixes as text | Apply fixes |
| Runs as an MCP server for agents | Handle every codec's retag path (H.264 and HEVC only) |

The roadmap is in [ROADMAP.md](../ROADMAP.md).

## How we'll know it's working

- It agrees with ground truth on the zoo (measured in the test suite).
- It says "inconclusive" instead of guessing on content that can't tell us (also tested).
- Strangers file issues with real files where it was wrong. Every one of those becomes a new zoo case.
