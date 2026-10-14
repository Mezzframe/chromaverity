"""Layer 2: look at the pixels and ask whether they agree with the label.

This is the part existing open tools don't do, and the reason the repo
exists. Each check here follows the same pattern:

    measure  (FFmpeg filter, deterministic, cheap)
       |
    classify (pure Python function, no I/O, fully unit-tested)
       |
    Finding  (verdict + confidence + the raw numbers)

Keeping measure and classify apart means the classifier can be tested with
made-up numbers, and later swapped for a learned model without touching the
measurement code (docs/adr/0003-measure-then-classify.md).

v0.1 ships range only. Transfer (PQ vs SDR) and matrix (601 vs 709) are on the
roadmap; matrix is hard and may end as a published negative result.
"""
