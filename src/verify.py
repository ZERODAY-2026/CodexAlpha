from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class QuoteVerification:
    clause_id: str
    quote: str
    normalized_quote: str
    match_found: bool
    start_offset: int | None = None
    end_offset: int | None = None


def _normalized_with_offsets(value: str) -> tuple[str, list[int]]:
    normalized: list[str] = []
    offsets: list[int] = []
    in_whitespace = False

    for index, character in enumerate(value):
        if character.isspace():
            if normalized and not in_whitespace:
                normalized.append(" ")
                offsets.append(index)
            in_whitespace = True
            continue
        normalized.append(character.casefold())
        offsets.extend([index] * len(character.casefold()))
        in_whitespace = False

    if normalized and normalized[-1] == " ":
        normalized.pop()
        offsets.pop()
    return "".join(normalized), offsets


def verify_quote(clause_text: str, quote: str) -> QuoteVerification:
    normalized_quote, _ = _normalized_with_offsets(quote.strip())
    normalized_clause, offsets = _normalized_with_offsets(clause_text)
    match_index = normalized_clause.find(normalized_quote) if normalized_quote else -1
    if match_index < 0:
        return QuoteVerification("", quote, normalized_quote, False)

    end_index = match_index + len(normalized_quote)
    return QuoteVerification(
        clause_id="",
        quote=quote,
        normalized_quote=normalized_quote,
        match_found=True,
        start_offset=offsets[match_index],
        end_offset=offsets[end_index - 1] + 1,
    )


def verify_clause_quote(clause_id: str, clause_text: str, quote: str) -> QuoteVerification:
    result = verify_quote(clause_text, quote)
    result.clause_id = clause_id
    return result


def pass_rate(verified: list[QuoteVerification]) -> dict[str, int | float]:
    total = len(verified)
    passed = sum(1 for item in verified if item.match_found)
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "rate": passed / total if total else 0.0,
    }
