from src.ingest import load_document
from src.segment import segment_document


def test_numbered_clause_heading_does_not_split_first_letter_from_line():
    document = load_document(
        b"1. Lease Term. The tenant shall pay rent monthly.\n\n"
        b"2. Notice. Either party may give 30 days written notice.",
        filename="agreement.txt",
    )
    segmented = segment_document(document)
    assert len(segmented.clauses) == 2
    assert segmented.clauses[0].text.startswith("1. Lease Term.")
    assert segmented.clauses[1].text.startswith("2. Notice.")
