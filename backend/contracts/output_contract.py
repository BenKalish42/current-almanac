"""
Output Contract — Python runtime mirror.

Source of truth: data/contracts/forbidden.json (loaded at import).
Mirror of src/contracts/outputContract.ts.

Wraps every backend LLM call so that Current's spec is enforced
identically on the server and the client.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

# data/contracts/forbidden.json lives at the repo root
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_FORBIDDEN_PATH = _REPO_ROOT / "data" / "contracts" / "forbidden.json"

with _FORBIDDEN_PATH.open("r", encoding="utf-8") as fh:
    _DATA = json.load(fh)

NON_ACTION_PHRASE: str = _DATA["non_action_phrase"]


@dataclass
class ContractViolation:
    category: str
    match: str
    index: int


@dataclass
class ContractAudit:
    ok: bool
    violations: list[ContractViolation]


# Compile regexes once.
_PATTERNS: list[tuple[str, re.Pattern[str]]] = []
for _category, _body in _DATA["categories"].items():
    for _p in _body["patterns"]:
        _PATTERNS.append((_category, re.compile(_p, re.IGNORECASE)))


def audit_compliance(text: str | None) -> ContractAudit:
    """Audit text against the Output Contract."""
    if not text:
        return ContractAudit(ok=True, violations=[])
    violations: list[ContractViolation] = []
    for category, rx in _PATTERNS:
        for m in rx.finditer(text):
            violations.append(
                ContractViolation(category=category, match=m.group(0), index=m.start())
            )
    return ContractAudit(ok=len(violations) == 0, violations=violations)


def enforce_compliance(text: str | None) -> str:
    """Last-resort redaction. Replaces matches with [redacted]."""
    if not text:
        return text or ""
    out = text
    for _, rx in _PATTERNS:
        out = rx.sub("[redacted]", out)
    return out


def format_violations(violations: Iterable[ContractViolation]) -> str:
    parts = [f'[{v.category}@{v.index}] "{v.match}"' for v in violations]
    return ", ".join(parts) if parts else "(none)"


OUTPUT_CONTRACT_SYSTEM: str = "\n".join(
    [
        "You are a description engine for a timing instrument named Current.",
        "",
        "ROLE",
        "- You describe the configuration of conditions in the present moment.",
        "- You clarify how effort interacts with those conditions.",
        "- You reduce friction, mistiming, and unnecessary force.",
        "",
        "YOU DO NOT",
        "- predict outcomes.",
        "- prescribe actions.",
        "- assign meaning, morality, or destiny.",
        "- recompute math (BaZi pillars, hexagrams, ayanamsa, Lagna, ganzhi). The provided JSON is canonical.",
        "",
        "OUTPUT CONTRACT (strict)",
        "Every reply must:",
        "  - describe current conditions,",
        "  - identify dominant dynamics (what is increasing / decreasing),",
        "  - describe the interaction pattern (what happens if force is applied),",
        "  - optionally describe capacity interaction.",
        "",
        "Every reply must avoid:",
        "  - instructions ('you should', 'do this', 'try to').",
        "  - predictions ('will happen', 'is going to').",
        "  - moral framing ('good day', 'bad day', 'auspicious to').",
        "  - destiny / agency ('the universe wants', 'your destiny', 'karmic').",
        "  - mystical inflation ('ancient wisdom', 'poetic', 'bridge ancient').",
        "",
        "TONE",
        "  - neutral, precise, compressive (high signal, low language inflation).",
        "  - no urgency, no reward language, no engagement loops.",
        "",
        "VOCABULARY (preferred)",
        "  Flow, Resistance, Pressure, Timing, Direction, Phase, Capacity, Load,",
        "  Auspiciousness (= low friction), Misalignment Signals, Non-action.",
        "",
        "WEAK SIGNAL",
        "  If the payload features are weak or contradictory, return exactly:",
        f'  "{NON_ACTION_PHRASE}"',
        "  and stop.",
        "",
        "FAILURE MODES TO ACTIVELY PREVENT",
        "  - decision outsourcing,",
        "  - compulsive checking,",
        "  - confirmation bias loops,",
        "  - green-light seeking.",
        "",
        "If asked for a recommendation, refuse and describe instead.",
    ]
)


__all__ = [
    "audit_compliance",
    "enforce_compliance",
    "format_violations",
    "OUTPUT_CONTRACT_SYSTEM",
    "NON_ACTION_PHRASE",
    "ContractAudit",
    "ContractViolation",
]
