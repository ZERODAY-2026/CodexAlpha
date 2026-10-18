import shutil
from pathlib import Path

import pytest
import fitz

from src import ingest
from src.ingest import load_document


def _scanned_pdf(text):
    with fitz.open() as source:
        page = source.new_page(width=612, height=792)
        page.insert_text((72, 100), text, fontsize=18)
        image = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).tobytes("png")
    with fitz.open() as scanned:
        page = scanned.new_page(width=612, height=792)
        page.insert_image(page.rect, stream=image)
        return scanned.tobytes()


def test_empty_text_document_raises_helpful_error():
    with pytest.raises(ValueError, match="empty|no extractable"):
        load_document(b"", filename="empty.txt")


def test_garbled_pdf_fails_cleanly():
    with pytest.raises(ValueError, match="no extractable text|PDF"):
        load_document(b"not-a-pdf", filename="bad.pdf")


def test_text_pdf_preserves_page_number():
    with fitz.open() as pdf:
        page = pdf.new_page()
        page.insert_text((72, 72), "A fictional agreement with a rent deadline on the fifth day.")
        raw_pdf = pdf.tobytes()
    document = load_document(raw_pdf, filename="agreement.pdf")
    assert document.total_pages == 1
    assert document.pages[0].page_number == 1
    assert "rent deadline" in document.pages[0].text


def test_image_only_pdf_is_read_with_tesseract_ocr():
    if not shutil.which("tesseract") or ingest._find_tessdata() is None:
        pytest.skip("Tesseract and English language data are not installed.")
    raw_pdf = _scanned_pdf(
        "Scanned contract rent is due on the fifth day of each month."
    )

    document = load_document(raw_pdf, filename="scanned.pdf")

    assert document.total_pages == 1
    assert document.pages[0].page_number == 1
    assert "rent is due on the fifth day" in document.pages[0].text.lower()


def test_empty_partial_ocr_falls_back_to_full_page_ocr(monkeypatch):
    monkeypatch.setattr(ingest, "_find_tessdata", lambda: Path("/local/tessdata"))

    class FakePage:
        def __init__(self):
            self.full_flags = []

        def get_textpage_ocr(self, *, full, **_kwargs):
            self.full_flags.append(full)
            return full

        def get_text(self, _kind, *, textpage):
            return "Recognized text from the scanned page." if textpage else ""

    page = FakePage()

    recognized = ingest._ocr_page(page, "")

    assert page.full_flags == [False, True]
    assert recognized == "Recognized text from the scanned page."


def test_scanned_pdf_explains_when_tesseract_is_unavailable(monkeypatch):
    monkeypatch.setattr(ingest, "_find_tessdata", lambda: None)
    raw_pdf = _scanned_pdf("Scanned agreement text requiring OCR.")

    with pytest.raises(ValueError, match="require Tesseract OCR"):
        load_document(raw_pdf, filename="scanned.pdf")


def test_image_only_or_blank_pdf_returns_clear_error():
    with fitz.open() as pdf:
        pdf.new_page()
        blank_pdf = pdf.tobytes()
    with pytest.raises(ValueError, match="no extractable text"):
        load_document(blank_pdf, filename="blank.pdf")
