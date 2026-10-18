import pytest
import fitz

from src.ingest import load_document


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


def test_image_only_or_blank_pdf_returns_clear_error():
    with fitz.open() as pdf:
        pdf.new_page()
        blank_pdf = pdf.tobytes()
    with pytest.raises(ValueError, match="no extractable text"):
        load_document(blank_pdf, filename="blank.pdf")
