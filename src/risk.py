from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    try:
        from src.segment import Clause
    except ImportError:  # pragma: no cover
        from segment import Clause

_VAGUE_TERMS = re.compile(
    r"\b(reasonable|as decided by|at (?:the )?sole discretion|"
    r"as determined by|from time to time|in good faith)\b",
    re.IGNORECASE,
)
_UNILATERAL_TERMS = re.compile(
    r"\b(?:employer|landlord|company|tenant|employee)\s+may\b",
    re.IGNORECASE,
)


def detect_risks(clause_text: str, *, clause_id: str = "", page: int = 0) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []
    for match in _VAGUE_TERMS.finditer(clause_text):
        flags.append({
            "type": "vague wording",
            "severity": "medium",
            "quote": match.group(0),
            "clause_id": clause_id,
            "page": str(page),
        })
    for match in _UNILATERAL_TERMS.finditer(clause_text):
        sentence_start = max(clause_text.rfind(".", 0, match.start()), clause_text.rfind("\n", 0, match.start())) + 1
        sentence_end = min(
            [index for index in (clause_text.find(".", match.end()), clause_text.find("\n", match.end())) if index >= 0]
            or [len(clause_text)]
        )
        flags.append({
            "type": "possible one-sided discretion",
            "severity": "medium",
            "quote": clause_text[sentence_start:sentence_end + (sentence_end < len(clause_text))].strip(),
            "clause_id": clause_id,
            "page": str(page),
        })
    return flags


def audit_document(clauses: list[Clause]) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []
    local_law_topics = [
        ("notice period", re.compile(r"\bnotice\b", re.IGNORECASE)),
        ("security deposit limits", re.compile(r"\b(?:security\s+)?deposit\b", re.IGNORECASE)),
        ("non-compete", re.compile(r"\bnon[- ]?compete\b|\bcovenant not to compete", re.IGNORECASE)),
        ("stamp duty or registration", re.compile(r"\bstamp duty\b|\bregistration\b", re.IGNORECASE)),
        ("penalties", re.compile(r"\bpenalt(?:y|ies)\b|\blate fee\b|\bliquidated damages\b", re.IGNORECASE)),
    ]
    for clause in clauses:
        flags.extend(detect_risks(clause.text, clause_id=clause.id, page=clause.page))
        for topic, pattern in local_law_topics:
            match = pattern.search(clause.text)
            if not match:
                continue
            sentence_start = max(
                clause.text.rfind(".", 0, match.start()),
                clause.text.rfind("\n", 0, match.start()),
            ) + 1
            sentence_end = clause.text.find(".", match.end())
            if sentence_end < 0:
                sentence_end = len(clause.text)
            flags.append({
                "type": f"local-law-sensitive issue: {topic}",
                "severity": "medium",
                "quote": clause.text[sentence_start:sentence_end + (sentence_end < len(clause.text))].strip(),
                "clause_id": clause.id,
                "page": str(clause.page),
                "note": "Requirements can vary by jurisdiction; this app does not state the law.",
            })
    document_text = "\n".join(clause.text for clause in clauses)
    missing_checks = [
        (
            "notice period",
            re.compile(r"\bnotice\b", re.IGNORECASE),
            "high",
        ),
        (
            "deposit",
            re.compile(r"\bdeposit\b", re.IGNORECASE),
            "medium",
        ),
        (
            "dispute resolution",
            re.compile(r"\bdispute resolution\b|\bmediation\b|\barbitration\b", re.IGNORECASE),
            "low",
        ),
    ]
    for label, pattern, severity in missing_checks:
        if not pattern.search(document_text):
            flags.append({
                "type": f"missing {label}",
                "severity": severity,
                "quote": "absent from document",
                "clause_id": "",
                "page": "",
            })
    deposit_refund = re.search(
        r"\bdeposit\b.{0,120}\b(?:return(?:ed)?|refund(?:ed)?)\b"
        r"|\b(?:return(?:ed)?|refund(?:ed)?)\b.{0,120}\bdeposit\b",
        document_text,
        re.IGNORECASE,
    )
    deposit_refund_denial = re.search(
        r"\b(?:no|not|does not|doesn't|will not|won't)\b.{0,60}"
        r"\b(?:deposit.{0,60}(?:return|refund)|(?:return|refund).{0,60}deposit)\b",
        document_text,
        re.IGNORECASE,
    )
    if not deposit_refund or deposit_refund_denial:
        flags.append({
            "type": "missing deposit refund terms",
            "severity": "medium",
            "quote": "absent from document",
            "clause_id": "",
            "page": "",
        })

    periods: list[tuple[int, str, Clause, re.Match[str]]] = []
    for clause in clauses:
        if not re.search(r"\bnotice\b|\bterminat(?:e|ion)\b", clause.text, re.IGNORECASE):
            continue
        periods.extend(
            (int(match.group(1)), match.group(2).lower().rstrip("s"), clause, match)
            for match in re.finditer(r"\b(\d+)\s+(days?|weeks?|months?)\b", clause.text, re.IGNORECASE)
        )
    values_by_unit: dict[str, set[int]] = {}
    for value, unit, _, _ in periods:
        values_by_unit.setdefault(unit, set()).add(value)
    conflicting_units = {unit for unit, values in values_by_unit.items() if len(values) > 1}
    for value, unit, clause, match in periods:
        if unit not in conflicting_units:
            continue
        sentence_start = max(clause.text.rfind(".", 0, match.start()), clause.text.rfind("\n", 0, match.start())) + 1
        sentence_end = clause.text.find(".", match.end())
        if sentence_end < 0:
            sentence_end = len(clause.text)
        flags.append({
            "type": "potentially conflicting notice periods",
            "severity": "high",
            "quote": clause.text[sentence_start:sentence_end + (sentence_end < len(clause.text))].strip(),
            "clause_id": clause.id,
            "page": str(clause.page),
        })
    rank = {"high": 0, "medium": 1, "low": 2}
    return sorted(flags, key=lambda flag: rank.get(flag["severity"], 3))
