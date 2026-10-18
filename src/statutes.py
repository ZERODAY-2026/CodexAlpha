"""Optional local statutory background retrieval over a manually built subset."""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from rank_bm25 import BM25Okapi

try:
    from src.config import STATUTE_SUBSET_PATH
    from src.jurisdiction_warnings import JurisdictionWarning
    from src.retrieve import _tokenise
except ImportError:  # pragma: no cover
    from config import STATUTE_SUBSET_PATH
    from jurisdiction_warnings import JurisdictionWarning
    from retrieve import _tokenise


logger = logging.getLogger("legal_triage.statutes")
STATUTE_SNAPSHOT = "v2026.08"
STATUTORY_BACKGROUND_DISCLAIMER = (
    "Possibly relevant law (background only). It may not apply to your situation, may have been "
    "amended since this snapshot, and is not a conclusion about your document. Check with a "
    "qualified local professional."
)
STATUTE_ATTRIBUTION = (
    "Dataset: Open India Law by Vaquill AI, CC BY 4.0. Legislation text sourced from India Code."
)


# These are retrieval hints only. They do not identify which law governs a document.
RULE_SECTION_HINTS: dict[str, dict[str, Any]] = {
    "rental_rent_increase": {"scope": "rental", "acts": ("transfer of property act", "karnataka rent"), "sections": ("rent", "increase", "enhancement", "revision")},
    "rental_security_deposit": {"scope": "rental", "acts": ("transfer of property act", "karnataka rent"), "sections": ("deposit", "premium", "lessor", "lessee")},
    "rental_eviction_termination_notice": {"scope": "rental", "acts": ("karnataka rent", "transfer of property act"), "sections": ("recovery of possession", "notice", "determination", "eviction", "termination")},
    "rental_lock_in_period": {"scope": "rental", "acts": ("transfer of property act", "karnataka rent"), "sections": ("lease", "determination", "term")},
    "rental_maintenance_repairs": {"scope": "rental", "acts": ("transfer of property act", "karnataka rent"), "sections": ("repairs", "lessor", "lessee", "maintenance")},
    "rental_subletting": {"scope": "rental", "acts": ("transfer of property act", "karnataka rent"), "sections": ("sub lease", "under lease", "transfer", "lease")},
    "rental_stamp_duty_registration": {"scope": "rental", "acts": ("registration act", "indian stamp act"), "sections": ("lease", "registration", "stamp duty", "instruments")},
    "rental_late_payment_penalty": {"scope": "rental", "acts": ("karnataka rent", "transfer of property act"), "sections": ("rent", "arrears", "interest", "payment")},
    "employment_notice_termination": {"scope": "employment", "acts": ("industrial disputes act", "industrial employment standing orders"), "sections": ("notice", "termination", "discharge", "dismissal", "retrenchment")},
    "employment_probation": {"scope": "employment", "acts": ("industrial employment standing orders", "industrial disputes act"), "sections": ("probation", "termination", "service", "standing orders")},
    "employment_non_compete": {"scope": "employment", "acts": ("industrial employment standing orders", "contract labour act"), "sections": ("conditions of employment", "service", "employment", "contract")},
    "employment_hours_overtime": {"scope": "employment", "acts": ("code on wages", "karnataka shops and establishments"), "sections": ("working hours", "overtime", "hours of work", "wages")},
    "employment_leave": {"scope": "employment", "acts": ("karnataka shops and establishments", "payment of gratuity act"), "sections": ("leave", "holidays", "gratuity", "employment")},
    "employment_wages_deductions": {"scope": "employment", "acts": ("code on wages", "payment of gratuity act"), "sections": ("wages", "deductions", "payment", "salary")},
    "employment_bond_training_costs": {"scope": "employment", "acts": ("industrial employment standing orders", "contract labour act"), "sections": ("conditions of employment", "service", "contract", "employment")},
    "employment_confidentiality_ip": {"scope": "employment", "acts": ("industrial employment standing orders", "contract labour act"), "sections": ("conditions of employment", "service", "employment", "contract")},
}


@dataclass(frozen=True)
class StatuteSection:
    act_id: str
    title: str
    state: str
    year: int | None
    section_number: str
    section_title: str
    text: str
    act_status: str
    in_force: bool | None
    source_url: str
    mirror_url: str
    source_publisher: str
    snapshot: str


def _normalise(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


def _keywords_match(value: str, phrases: Iterable[str]) -> bool:
    tokens = set(_normalise(value).split())
    for phrase in phrases:
        phrase_tokens = _normalise(phrase).split()
        if phrase_tokens and all(token in tokens for token in phrase_tokens):
            return True
    return False


def _valid_record(record: Any) -> bool:
    if not isinstance(record, dict):
        return False
    required = ("act_id", "title", "state", "section_number", "section_title", "text")
    return all(isinstance(record.get(key), str) for key in required) and bool(record.get("title")) and bool(record.get("text"))


def _to_section(record: dict[str, Any]) -> StatuteSection:
    year_value = record.get("year")
    try:
        year = int(year_value) if year_value is not None else None
    except (TypeError, ValueError, OverflowError):
        year = None
    state = _normalise(record.get("state")).replace(" ", "-") or "central"
    in_force_value = record.get("in_force")
    in_force = in_force_value if isinstance(in_force_value, bool) else None
    return StatuteSection(
        act_id=record["act_id"],
        title=record["title"],
        state=state,
        year=year,
        section_number=record["section_number"],
        section_title=record["section_title"],
        text=record["text"],
        act_status=str(record.get("act_status") or "unknown"),
        in_force=in_force,
        source_url=str(record.get("source_url") or ""),
        mirror_url=str(record.get("mirror_url") or ""),
        source_publisher=str(record.get("source_publisher") or ""),
        snapshot=str(record.get("snapshot") or STATUTE_SNAPSHOT),
    )


def _excerpt(text: str, limit: int = 300) -> str:
    clean = text.strip()
    lines = clean.splitlines()
    if lines and lines[0].lstrip().startswith("Act:"):
        clean = "\n".join(lines[1:]).strip()
    if len(clean) <= limit:
        return clean
    cut = clean.rfind(" ", 0, limit - 1)
    if cut < limit // 2:
        cut = limit - 1
    return clean[:cut].rstrip() + "…"


class StatuteIndex:
    def __init__(self, sections: list[StatuteSection]) -> None:
        self.sections = sections
        corpus = [
            _tokenise(" ".join((section.title, section.section_title, section.text)))
            for section in sections
        ]
        self._bm25 = BM25Okapi(corpus) if corpus else None

    def get_statute_background(self, rule_id: str, doc_type: str) -> list[dict[str, Any]]:
        mapping = RULE_SECTION_HINTS.get(rule_id)
        if not mapping:
            return []
        scope = doc_type if doc_type in {"rental", "employment", "both"} else "both"
        if mapping["scope"] != "both" and scope not in {mapping["scope"], "both"}:
            return []
        if not self.sections or self._bm25 is None:
            return []

        act_hints = mapping["acts"]
        section_hints = mapping["sections"]
        candidates = [
            (index, section)
            for index, section in enumerate(self.sections)
            if _keywords_match(section.title, act_hints)
            and _keywords_match(section.section_title, section_hints)
        ]
        if not candidates:
            return []
        query = " ".join((*act_hints, *section_hints))
        query_tokens = _tokenise(query)
        scores = self._bm25.get_scores(query_tokens)
        ranked = sorted(
            candidates,
            key=lambda pair: (float(scores[pair[0]]), pair[1].title.casefold(), pair[1].section_number),
            reverse=True,
        )[:2]
        results: list[dict[str, Any]] = []
        for _, section in ranked:
            source_url = section.source_url or section.mirror_url
            item: dict[str, Any] = {
                "act_title": section.title,
                "state": section.state,
                "year": section.year,
                "section_number": section.section_number,
                "section_title": section.section_title,
                "excerpt": _excerpt(section.text),
                "status": section.act_status,
                "snapshot": section.snapshot,
            }
            if source_url:
                item["source_url"] = source_url
            results.append(item)
        return results


def load_statute_index(path: Path) -> StatuteIndex | None:
    try:
        if not path.is_file():
            logger.info("statute_background_disabled reason=missing_subset")
            return None
        records: list[StatuteSection] = []
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                record = json.loads(line)
                if not _valid_record(record):
                    raise ValueError("invalid subset record")
                records.append(_to_section(record))
        if not records:
            logger.info("statute_background_disabled reason=empty_subset")
            return None
        return StatuteIndex(records)
    except Exception:
        # Never include path contents, row text, or parser exception details in logs.
        logger.info("statute_background_disabled reason=unreadable_subset")
        return None


_DEFAULT_INDEX = load_statute_index(STATUTE_SUBSET_PATH)


def get_statute_background(rule_id: str, doc_type: str) -> list[dict[str, Any]]:
    if _DEFAULT_INDEX is None:
        return []
    return _DEFAULT_INDEX.get_statute_background(rule_id, doc_type)


def enrich_jurisdiction_warnings(
    warnings: list[JurisdictionWarning], doc_type: str
) -> list[dict[str, Any]]:
    """Attach only fixed-rule retrieval results; document text is never an input."""
    if _DEFAULT_INDEX is None:
        return warnings
    enriched: list[dict[str, Any]] = []
    for warning in warnings:
        item = dict(warning)
        background = get_statute_background(str(item.get("rule_id", "")), doc_type)
        item["statutory_background"] = background
        if background:
            item["statutory_snapshot"] = background[0]["snapshot"]
            item["statutory_disclaimer"] = STATUTORY_BACKGROUND_DISCLAIMER
        enriched.append(item)
    return enriched
