"""
src/ingest.py — load a PDF or plain-text file and return per-page text.

Rule 1 compliance: no data leaves this machine; all I/O is local file reads.
Rule 5 compliance: extracted text is treated as data (returned as strings),
                   never evaluated or executed.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

import fitz  # PyMuPDF

try:
    from src.config import SUPPORTED_EXTENSIONS
except ImportError:  # pragma: no cover
    from config import SUPPORTED_EXTENSIONS


@dataclass
class PageText:
    """Holds the raw text of a single page."""
    page_number: int   # 1-indexed
    text: str


@dataclass
class IngestedDocument:
    """All pages extracted from a single document."""
    source_name: str
    pages: list[PageText] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages)

    @property
    def total_pages(self) -> int:
        return len(self.pages)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_document(source: Union[str, Path, bytes], filename: str = "") -> IngestedDocument:
    """
    Load a PDF or TXT file and return an IngestedDocument.

    Parameters
    ----------
    source   : file path (str/Path) or raw bytes
    filename : original filename — used to detect extension when source is bytes
    """
    if isinstance(source, (str, Path)):
        path = Path(source)
        suffix = path.suffix.lower()
        name = path.name
        raw_bytes = path.read_bytes()
    elif isinstance(source, (bytes, bytearray)):
        suffix = Path(filename).suffix.lower() if filename else ""
        name = filename or "uploaded_document"
        raw_bytes = bytes(source)
    else:
        raise TypeError(f"Unsupported source type: {type(source)}")

    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{suffix}'. "
            f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    if suffix == ".pdf":
        return _load_pdf(raw_bytes, name)
    else:  # .txt
        return _load_txt(raw_bytes, name)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_pdf(raw_bytes: bytes, name: str) -> IngestedDocument:
    doc = IngestedDocument(source_name=name)
    try:
        with fitz.open(stream=raw_bytes, filetype="pdf") as pdf:
            for idx, page in enumerate(pdf, start=1):
                text = page.get_text("text")
                text = _clean(text)
                if text:
                    doc.pages.append(PageText(page_number=idx, text=text))
    except Exception as exc:  # PyMuPDF raises FzErrorFormat on invalid PDFs.
        raise ValueError("PDF appears to contain no extractable text or is malformed.") from exc
    if not doc.pages:
        raise ValueError("PDF appears to contain no extractable text (may be scanned/image-only).")
    return doc


def _load_txt(raw_bytes: bytes, name: str) -> IngestedDocument:
    text = raw_bytes.decode("utf-8", errors="replace")
    # Treat each ~page-worth of content as a "page" (split on form-feeds, else single page)
    raw_pages = text.split("\x0c")  # form-feed character = page break in many text exports
    doc = IngestedDocument(source_name=name)
    for idx, page_text in enumerate(raw_pages, start=1):
        cleaned = _clean(page_text)
        if cleaned:
            doc.pages.append(PageText(page_number=idx, text=cleaned))
    if not doc.pages:
        raise ValueError("Text file appears to be empty.")
    return doc


def _clean(text: str) -> str:
    """Normalise whitespace; strip trailing/leading blanks."""
    import re
    # Collapse runs of 3+ newlines to double newline
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
