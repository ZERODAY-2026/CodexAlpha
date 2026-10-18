"""Deterministic, generic background notices for jurisdiction-sensitive topics."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, TypedDict

try:
    from src.segment import Clause
except ImportError:  # pragma: no cover
    from segment import Clause


class TriggeringClause(TypedDict):
    clause_id: str
    page: int


class JurisdictionWarning(TypedDict):
    rule_id: str
    clause_type: str
    warning_text: str
    triggering_clauses: list[TriggeringClause]


@dataclass(frozen=True)
class WarningRule:
    id: str
    clause_type: str
    keywords: tuple[str, ...]
    document_scope: str
    warning_text: str


_COMMON = "This is background only, not from your document and not professional advice. Check your local rules with a qualified local professional."


RULES: tuple[WarningRule, ...] = (
    WarningRule("rental_rent_increase", "rent increase or revision", ("rent increase", "increase in rent", "increase the rent", "rent revision", "rent escalation", r"re:rent.{0,35}(?:increas|revis|escalat)", r"re:(?:increas|revis|escalat).{0,35}rent"), "rental", f"Rules on rent increases can vary by state and by the type of tenancy. {_COMMON}"),
    WarningRule("rental_security_deposit", "security deposit and refund", ("security deposit", "refundable deposit", "deposit refund", r"re:deposit.{0,30}(?:refund|return|deduct)"), "rental", f"Rules on security deposits and refunds can vary by state and by the type of tenancy. {_COMMON}"),
    WarningRule("rental_eviction_termination_notice", "eviction or termination notice", ("eviction notice", "notice to vacate", "termination notice", "notice of termination", "terminate the tenancy", "end the tenancy", "notice period", "days' notice", "days notice"), "rental", f"Rules on eviction, termination, and notice can vary by state and by the type of tenancy. {_COMMON}"),
    WarningRule("rental_lock_in_period", "lock-in period", ("lock-in period", "lock in period", "lock-in", "lock in", "minimum stay", "minimum tenancy"), "rental", f"Rules on lock-in periods can vary by state and by the type of tenancy. {_COMMON}"),
    WarningRule("rental_maintenance_repairs", "maintenance and repairs", ("maintenance", "repairs", "repair cost", "repair costs", "structural repair", "upkeep of the premises"), "rental", f"Rules on maintenance and repairs can vary by state and by the type of tenancy. {_COMMON}"),
    WarningRule("rental_subletting", "subletting", ("sublet", "subletting", "sub-lease", "sublease", "underlet", "underletting"), "rental", f"Rules on subletting can vary by state and by the type of tenancy. {_COMMON}"),
    WarningRule("rental_stamp_duty_registration", "stamp duty and registration", ("stamp duty", "registration of this agreement", "registered agreement", "register this agreement", "registration fee", "registration charges"), "rental", f"Rules on stamp duty and registration can vary by state and by the type of tenancy. {_COMMON}"),
    WarningRule("rental_late_payment_penalty", "late-payment penalty", ("late payment penalty", "late-payment penalty", "late fee", "late payment charge", "overdue rent", "interest on late", "penalty for late"), "rental", f"Rules on late-payment penalties can vary by state and by the type of tenancy. {_COMMON}"),
    WarningRule("employment_notice_termination", "notice period or termination", ("notice period", "notice of termination", "termination of employment", "terminate employment", "employment may be terminated", "resignation notice", "days' notice", "days notice"), "employment", f"Rules on employment notice and termination can vary by state and by the type of work. {_COMMON}"),
    WarningRule("employment_probation", "probation", ("probation", "probationary period", "probation period"), "employment", f"Rules on probation can vary by state and by the type of work. {_COMMON}"),
    WarningRule("employment_non_compete", "non-compete", ("non-compete", "noncompete", "non compete", "restraint of trade", "competing business"), "employment", f"Rules on non-compete terms can vary by state and by the type of work. {_COMMON}"),
    WarningRule("employment_hours_overtime", "working hours and overtime", ("working hours", "hours of work", "overtime", "over-time", "extra hours", "hours per week"), "employment", f"Rules on working hours and overtime can vary by state and by the type of work. {_COMMON}"),
    WarningRule("employment_leave", "leave", ("annual leave", "paid leave", "sick leave", "maternity leave", "leave entitlement", "leave days", "vacation leave"), "employment", f"Rules on workplace leave can vary by state and by the type of work. {_COMMON}"),
    WarningRule("employment_wages_deductions", "wages and deductions", ("wages", "salary deduction", "deduction from salary", "deductions from wages", "withhold salary", "withholding wages", "pay shall be", "monthly salary"), "employment", f"Rules on wages and deductions can vary by state and by the type of work. {_COMMON}"),
    WarningRule("employment_bond_training_costs", "bond or training-cost recovery", ("employment bond", "service bond", "training cost", "training costs", "training-cost", "recover training", "repay training", "cost of training"), "employment", f"Rules on employment bonds and training-cost recovery can vary by state and by the type of work. {_COMMON}"),
    WarningRule("employment_confidentiality_ip", "confidentiality and IP assignment", ("confidential information", "confidentiality", "intellectual property", "ip assignment", "assigns all rights", "work product", "inventions created", "ownership of inventions"), "employment", f"Rules on confidentiality and IP assignment can vary by state and by the type of work. {_COMMON}"),
)


def infer_document_type(clauses: Iterable[Clause]) -> str:
    """Infer a broad scope from document vocabulary; ambiguous text uses both."""
    text = " ".join(clause.text.lower() for clause in clauses)
    rental = sum(term in text for term in ("tenant", "landlord", "premises", "tenancy", "rent", "lease"))
    employment = sum(term in text for term in ("employee", "employer", "employment", "salary", "workplace", "job"))
    if rental and employment:
        return "both"
    if rental:
        return "rental"
    if employment:
        return "employment"
    return "both"


def detect_jurisdiction_warnings(clauses: Iterable[Clause], doc_type: str) -> list[JurisdictionWarning]:
    """Return fixed warnings for matching source clauses, in registry order."""
    source_clauses = list(clauses)
    scope = doc_type.lower() if isinstance(doc_type, str) else ""
    if scope not in {"rental", "employment", "both"}:
        scope = "both"
    results: list[JurisdictionWarning] = []
    for rule in RULES:
        if scope != "both" and rule.document_scope not in {scope, "both"}:
            continue
        triggers = [
            {"clause_id": clause.id, "page": clause.page}
            for clause in source_clauses
            if any(_matches(keyword, clause.text) for keyword in rule.keywords)
        ]
        if triggers:
            results.append({
                "rule_id": rule.id,
                "clause_type": rule.clause_type,
                "warning_text": rule.warning_text,
                "triggering_clauses": triggers,
            })
    return results


def _matches(keyword: str, text: str) -> bool:
    if keyword.startswith("re:"):
        return re.search(keyword[3:], text, re.IGNORECASE) is not None
    return keyword in text.lower()
