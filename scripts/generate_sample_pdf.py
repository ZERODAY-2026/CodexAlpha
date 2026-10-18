#!/usr/bin/env python3
"""Generate the self-written, text-searchable fictional rental PDF sample."""
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "sample_docs" / "rental_agreement_sample.pdf"
TEXT = """FICTIONAL RENTAL AGREEMENT

1. Parties. Morgan Reed rents the apartment at 14 Cedar Lane from Avery Park.

2. Rent. The tenant shall pay rent of $1,500 per month, due on the 5th day of each month.

3. Term. The tenancy begins on 1 June 2026 and continues for twelve months.

4. Notice. Either party may end the agreement by giving 30 days' written notice.

5. Deposit. The tenant pays a security deposit of $1,000. The landlord will return the deposit within 14 days after the tenancy ends, less any itemised repair costs.

6. Repairs. The tenant must report urgent repair needs to the landlord as soon as reasonably possible."""


def main() -> None:
    with fitz.open() as document:
        page = document.new_page()
        remaining_height = page.insert_textbox(
            fitz.Rect(64, 64, 531, 778),
            TEXT,
            fontname="helv",
            fontsize=11,
            lineheight=1.35,
        )
        if remaining_height < 0:
            raise RuntimeError("The sample text did not fit on a single PDF page.")
        DESTINATION.write_bytes(document.tobytes(garbage=4, deflate=True))
    print(f"Generated {DESTINATION}")


if __name__ == "__main__":
    main()
