"""
src/segment.py — split ingested pages into clause/section chunks.

Strategy (in priority order):
  1. Numbered clause patterns  e.g. "1.", "1.1", "Clause 3:", "Section IV"
  2. ALL-CAPS heading lines    e.g. "PAYMENT TERMS"
  3. Title-case heading lines  e.g. "Termination of Employment"
  4. Paragraph fallback        split on blank lines, then size-limit chunks

Each chunk becomes a Clause dataclass with a stable id, page number, and
exact source text (Rule 3: quotes must be verbatim from these texts).

Rule 5 compliance: text content is never eval'd; regex operates only on
                   whitespace/punctuation patterns, not on content values.
"""
from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass, field
from typing import Optional

try:
    from src.config import FALLBACK_CHUNK_OVERLAP, FALLBACK_CHUNK_SIZE, MIN_CHUNK_CHARS
    from src.ingest import IngestedDocument, PageText
except ImportError:  # pragma: no cover
    from config import FALLBACK_CHUNK_OVERLAP, FALLBACK_CHUNK_SIZE, MIN_CHUNK_CHARS
    from ingest import IngestedDocument, PageText


@dataclass
class Clause:
    id: str            # e.g. "p2-c003"
    page: int          # 1-indexed source page
    heading: str       # detected heading, or first 60 chars of text
    text: str          # exact verbatim text of this clause/chunk


@dataclass
class SegmentedDocument:
    source_name: str
    clauses: list[Clause] = field(default_factory=list)

    def get_clause(self, clause_id: str) -> Optional[Clause]:
        for c in self.clauses:
            if c.id == clause_id:
                return c
        return None


# ---------------------------------------------------------------------------
# Heading detection patterns
# ---------------------------------------------------------------------------

_NUMBERED_RE = re.compile(
    r"^(?:\d{1,2}(?:\.\d{1,2}){0,2}\.?\s+[^\r\n]+"
    r"|(?:Clause|Section|Article|Schedule)\s+[\dIVXivx]+\.?[^\r\n]*)",
    re.MULTILINE,
)

_ALLCAPS_RE = re.compile(
    r"^([A-Z][A-Z\s\-\/]{4,})$",
    re.MULTILINE,
)

_TITLECASE_RE = re.compile(
    r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,6})\s*$",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def segment_document(doc: IngestedDocument) -> SegmentedDocument:
    """Split an IngestedDocument into Clause chunks."""
    result = SegmentedDocument(source_name=doc.source_name)
    clause_counter = 0

    for page in doc.pages:
        chunks = _split_page(page.text)
        for heading, body in chunks:
            full_text = (f"{heading}\n{body}" if heading else body).strip()
            if len(full_text) < MIN_CHUNK_CHARS:
                continue
            clause_counter += 1
            cid = f"p{page.page_number}-c{clause_counter:03d}"
            display_heading = heading if heading else full_text[:60].replace("\n", " ")
            result.clauses.append(
                Clause(
                    id=cid,
                    page=page.page_number,
                    heading=display_heading,
                    text=full_text,
                )
            )

    return result


# ---------------------------------------------------------------------------
# Internal split logic
# ---------------------------------------------------------------------------

def _split_page(text: str) -> list[tuple[str, str]]:
    """Return list of (heading, body) tuples from a page of text."""
    # Try numbered patterns first (highest precision)
    chunks = _split_by_pattern(text, _NUMBERED_RE)
    if len(chunks) > 1:
        return chunks

    # Try ALL-CAPS headings
    chunks = _split_by_pattern(text, _ALLCAPS_RE)
    if len(chunks) > 1:
        return chunks

    # Try Title-Case headings
    chunks = _split_by_pattern(text, _TITLECASE_RE)
    if len(chunks) > 1:
        return chunks

    # Fallback: paragraph / size-based chunking
    return _paragraph_chunks(text)


def _split_by_pattern(text: str, pattern: re.Pattern) -> list[tuple[str, str]]:
    """
    Split text by a heading regex.  Returns [(heading, body), ...].
    A leading preamble before the first heading is kept as ("", preamble).
    """
    matches = list(pattern.finditer(text))
    if not matches:
        return []

    chunks: list[tuple[str, str]] = []
    prev_end = 0

    # Preamble before first heading
    preamble = text[:matches[0].start()].strip()
    if len(preamble) >= MIN_CHUNK_CHARS:
        chunks.append(("", preamble))

    for i, m in enumerate(matches):
        heading = m.group(0).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()
        chunks.append((heading, body))

    return chunks


def _paragraph_chunks(text: str) -> list[tuple[str, str]]:
    """Split on blank lines, then cap each chunk at FALLBACK_CHUNK_SIZE."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[tuple[str, str]] = []

    buffer = ""
    for para in paragraphs:
        if len(buffer) + len(para) + 2 <= FALLBACK_CHUNK_SIZE:
            buffer = (buffer + "\n\n" + para).strip()
        else:
            if buffer:
                chunks.append(("", buffer))
            # If a single paragraph exceeds chunk size, slice with overlap
            if len(para) > FALLBACK_CHUNK_SIZE:
                for start in range(0, len(para), FALLBACK_CHUNK_SIZE - FALLBACK_CHUNK_OVERLAP):
                    slice_ = para[start : start + FALLBACK_CHUNK_SIZE].strip()
                    if slice_:
                        chunks.append(("", slice_))
                buffer = ""
            else:
                buffer = para

    if buffer:
        chunks.append(("", buffer))

    return chunks if chunks else [("", text.strip())]
