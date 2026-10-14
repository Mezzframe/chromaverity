"""One shape for everything the tool reports.

Every check (lint, diff, essence) returns a list of Finding objects. Keeping
one shape means the CLI, the JSON report and the MCP server never need to
know which check produced a result.

Finding IDs are stable and grouped by layer, like error codes on a router.
"CT" stands for color tag:

    CT1xx  label lint      (one file, tags only)
    CT2xx  label diff      (two files, tags only)
    CT3xx  essence checks  (pixels vs label)

Never reuse an ID for a different meaning. Retire it instead. Scripts and
agents key off these codes (docs/05-report-format.md).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    # str subclass so json.dumps writes "warn", not "Severity.WARN".
    ERROR = "error"  # label and pixels disagree, with strong evidence
    WARN = "warn"    # likely wrong, or wrong for most deliveries
    INFO = "info"    # worth knowing; may be intentional

    @property
    def rank(self) -> int:
        return {"error": 2, "warn": 1, "info": 0}[self.value]


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Finding:
    id: str
    severity: Severity
    title: str
    detail: str
    # Raw numbers behind the claim. An agent or a person should be able to
    # check the reasoning without rerunning the tool.
    evidence: dict[str, Any] = field(default_factory=dict)
    confidence: Confidence = Confidence.HIGH
    # Short pointers toward a fix. Actual commands live in fixes.py.
    fix_hint: str | None = None

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity.value
        d["confidence"] = self.confidence.value
        return d


def worst(findings: list[Finding]) -> Severity | None:
    """Highest severity in a list, used for the CLI exit code."""
    if not findings:
        return None
    return max((f.severity for f in findings), key=lambda s: s.rank)
