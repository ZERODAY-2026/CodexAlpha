"""
src/retrieve.py — BM25 keyword retrieval over segmented clauses.

Rule 1 compliance: purely local computation; rank_bm25 runs in-process.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from rank_bm25 import BM25Okapi

try:
    from src.config import BM25_TOP_K
    from src.segment import Clause, SegmentedDocument
except ImportError:  # pragma: no cover
    from config import BM25_TOP_K
    from segment import Clause, SegmentedDocument


@dataclass
class RetrievalResult:
    clause: Clause
    score: float


class ClauseRetriever:
    """BM25 index built over the clauses of a single document."""

    def __init__(self, segmented: SegmentedDocument) -> None:
        self._clauses = segmented.clauses
        tokenised = [_tokenise(c.text) for c in self._clauses]
        self._bm25 = BM25Okapi(tokenised)

    # ------------------------------------------------------------------
    def search(self, query: str, top_k: int = BM25_TOP_K) -> list[RetrievalResult]:
        """Return up to top_k clauses most relevant to query."""
        if not self._clauses:
            return []

        tokens = _tokenise(query)
        scores = self._bm25.get_scores(tokens)
        k = min(top_k, len(self._clauses))
        query_terms = set(tokens)
        overlaps = [
            len(query_terms.intersection(_tokenise(clause.text)))
            for clause in self._clauses
        ]
        ranked_indices = sorted(
            range(len(scores)),
            key=lambda i: (scores[i], overlaps[i]),
            reverse=True,
        )[:k]

        results = []
        for idx in ranked_indices:
            if scores[idx] > 0 or overlaps[idx] > 0:
                score = float(scores[idx]) if scores[idx] > 0 else overlaps[idx] / max(len(query_terms), 1)
                results.append(RetrievalResult(clause=self._clauses[idx], score=score))

        return results

    def get_all_clauses(self) -> list[Clause]:
        return list(self._clauses)


# ---------------------------------------------------------------------------
# Tokeniser
# ---------------------------------------------------------------------------

def _tokenise(text: str) -> list[str]:
    """Lowercase, split on non-alphanumeric, remove single-char tokens."""
    tokens = re.split(r"[^a-zA-Z0-9]+", text.lower())
    return [t for t in tokens if len(t) > 1]
