"""
src/ingest.py — load a PDF or plain-text file and return per-page text.

Rule 1 compliance: no data leaves this machine; all I/O is local file reads.
Rule 5 compliance: extracted text is treated as data (returned as strings),
                   never evaluated or executed.
"""
from __future__ import annotations

import io
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

import fitz  # PyMuPDF

try:
    from src.config import SUPPORTED_EXTENSIONS
except ImportError:  # pragma: no cover
    from config import SUPPORTED_EXTENSIONS

_OCR_TEXT_THRESHOLD = 100
_OCR_DPI = 200


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
                if len(text) < _OCR_TEXT_THRESHOLD and page.get_images():
                    text = _ocr_page(page, text)
                if text:
                    doc.pages.append(PageText(page_number=idx, text=text))
    except _TesseractUnavailableError:
        raise
    except Exception as exc:  # PyMuPDF raises FzErrorFormat on invalid PDFs.
        raise ValueError("PDF appears to contain no extractable text or is malformed.") from exc
    if not doc.pages:
        raise ValueError("PDF appears to contain no extractable text after OCR (it may be blank).")
    return doc


class _TesseractUnavailableError(ValueError):
    pass


def _ocr_page(page: fitz.Page, existing_text: str) -> str:
    tessdata = _find_tessdata()
    if tessdata is None:
        raise _TesseractUnavailableError(
            "Scanned PDF pages require Tesseract OCR and its English language data. "
            "Install Tesseract, then set TESSDATA_PREFIX to its tessdata directory if "
            "the app cannot find it automatically."
        )
    try:
        text_page = page.get_textpage_ocr(
            language="eng",
            dpi=_OCR_DPI,
            full=False,
            tessdata=str(tessdata),
        )
        recognized = _clean(page.get_text("text", textpage=text_page))
        if len(recognized) < _OCR_TEXT_THRESHOLD:
            # Some scanned pages have image transforms that partial OCR cannot read.
            full_text_page = page.get_textpage_ocr(
                language="eng",
                dpi=_OCR_DPI,
                full=True,
                tessdata=str(tessdata),
            )
            full_recognized = _clean(page.get_text("text", textpage=full_text_page))
            if len(full_recognized) > len(recognized):
                recognized = full_recognized
    except RuntimeError as exc:
        raise _TesseractUnavailableError(
            "Tesseract OCR could not process this scanned PDF page. Check that Tesseract "
            "and its English language data are installed correctly."
        ) from exc
    return recognized if len(recognized) > len(existing_text) else existing_text


def _find_tessdata() -> Path | None:
    candidates: list[Path] = []
    configured = os.environ.get("TESSDATA_PREFIX")
    if configured:
        configured_path = Path(configured).expanduser()
        candidates.extend((configured_path, configured_path / "tessdata"))

    executable = shutil.which("tesseract")
    if executable:
        binary_dir = Path(executable).resolve().parent
        candidates.extend(
            (
                binary_dir / "tessdata",
                binary_dir.parent / "share" / "tessdata",
            )
        )

    candidates.extend(
        Path(path)
        for path in (
            "/usr/share/tesseract-ocr/5/tessdata",
            "/usr/share/tesseract-ocr/4.00/tessdata",
            "/usr/share/tessdata",
            "/usr/local/share/tessdata",
            "/opt/homebrew/share/tessdata",
            r"C:\Program Files\Tesseract-OCR\tessdata",
        )
    )
    for candidate in candidates:
        if (candidate / "eng.traineddata").is_file():
            return candidate
    return None


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
