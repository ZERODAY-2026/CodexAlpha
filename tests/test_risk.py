from src.risk import audit_document
from src.segment import Clause


def test_risk_audit_flags_vague_terms_missing_items_and_conflicting_periods():
    clauses = [
        Clause(
            id="p1-c001",
            page=1,
            heading="Repairs",
            text="The landlord may require reasonable repairs.",
        ),
        Clause(
            id="p1-c002",
            page=1,
            heading="Notice",
            text="Either party may end the agreement with 30 days' written notice.",
        ),
        Clause(
            id="p1-c003",
            page=1,
            heading="Ending",
            text="The tenant must give 60 days' notice to end the agreement.",
        ),
    ]
    risks = audit_document(clauses)
    kinds = {risk["type"] for risk in risks}
    assert "vague wording" in kinds
    assert "missing deposit refund terms" in kinds
    assert "potentially conflicting notice periods" in kinds
    assert all("quote" in risk for risk in risks)
