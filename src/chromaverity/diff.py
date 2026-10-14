"""Layer 1b: compare the label before and after one hop.

A "hop" is anything that rewrites a file: a transcode, a cloud encoder, an
NLE export, an AI upscaler, a CDN packager. Labels get dropped or rewritten
at hops far more often than pixels get damaged, and nobody notices until a
viewer says the picture looks washed out.

Broadcast analogy: this is checking the tally and the format setting on both
sides of a frame sync. If the input says 1080i59.94 709 and the output says
nothing, something in the box made a decision you didn't.
"""

from __future__ import annotations

from chromaverity.findings import Finding, Severity
from chromaverity.tags import TAG_FIELDS, ColorTags, friendly


def diff(before: ColorTags, after: ColorTags) -> list[Finding]:
    findings: list[Finding] = []
    for name in TAG_FIELDS:
        a, b = getattr(before, name), getattr(after, name)
        if a == b:
            continue
        if a is not None and b is None:
            sev, verb = Severity.WARN, "dropped"
        elif a is None and b is not None:
            sev, verb = Severity.INFO, "added"
        else:
            sev, verb = Severity.WARN, "changed"
        # bit depth and pixel format changes are often deliberate (10-bit master
        # to 8-bit web). Report them, but at info level.
        if name in ("pix_fmt", "bit_depth"):
            sev = Severity.INFO
        findings.append(
            Finding(
                id="CT201",
                severity=sev,
                title=f"{name} {verb} at this hop",
                detail=f"{name}: {friendly(a) if name != 'bit_depth' else a} -> "
                f"{friendly(b) if name != 'bit_depth' else b}",
                evidence={"field": name, "before": a, "after": b},
                fix_hint=(
                    "Pass the flag explicitly on the encoder, or retag the output "
                    "(see `chromaverity inspect` on the output for a proposed command)."
                    if verb != "added"
                    else None
                ),
            )
        )

    for name, label in (
        ("has_mastering_display", "mastering display metadata"),
        ("has_content_light_level", "content light level metadata"),
    ):
        if getattr(before, name) and not getattr(after, name):
            findings.append(
                Finding(
                    id="CT202",
                    severity=Severity.WARN,
                    title=f"HDR {label} dropped",
                    detail=(
                        f"The input carried {label} and the output does not. HDR displays "
                        "will tone-map with their own defaults."
                    ),
                    evidence={"field": name, "before": True, "after": False},
                )
            )
    return findings
