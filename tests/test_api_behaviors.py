import logging

from src.analyze import answer_question, structured_answer_question
from src.segment import Clause


class FakeClient:
    def generate(self, prompt: str, expect_json: bool = False):
        return "The document does not address this."

    def generate_json(self, prompt: str):
        clause_id = "p1-c001 | page 1" if "When is rent due?" in prompt else "p1-c001"
        return {
            "answer_status": "answered",
            "stated_in_document": [
                {
                    "claim": "The tenant has a payment obligation.",
                    "quote": "The tenant shall pay rent each month.",
                    "clause_id": clause_id,
                },
                {
                    "claim": "Fabricated claim.",
                    "quote": "The rent is refundable.",
                    "clause_id": "p1-c001",
                },
            ],
            "possible_interpretations": [],
            "concerns": [],
            "uncertainty_notes": [],
            "escalation": "",
        }


def test_document_silent_question():
    answer = answer_question("When does the employee start?", [], client=FakeClient())
    assert "does not address this" in answer.lower()


def test_fabricated_quote_is_dropped_and_verified_quote_survives():
    clause = Clause(
        id="p1-c001",
        page=1,
        heading="Payment",
        text="The tenant shall pay rent each month.",
    )
    answer = structured_answer_question(
        "What does the tenant have to do?", [clause], client=FakeClient()
    )
    assert len(answer["stated_in_document"]) == 1
    item = answer["stated_in_document"][0]
    assert item["verified"] is True
    assert item["quote"] == "The tenant shall pay rent each month."
    assert item["quote_start"] == 0


def test_model_clause_id_with_page_annotation_is_canonicalized_safely():
    clause = Clause(
        id="p1-c001",
        page=1,
        heading="Payment",
        text="The tenant shall pay rent each month.",
    )
    answer = structured_answer_question(
        "When is rent due?", [clause], client=FakeClient()
    )
    assert answer["stated_in_document"][0]["clause_id"] == "p1-c001"


def test_enforceability_question_returns_refusal_with_cited_source():
    clause = Clause(
        id="p2-c004",
        page=2,
        heading="Termination",
        text="The employer may terminate the agreement with 14 days' notice.",
    )
    answer = structured_answer_question(
        "Is this termination clause enforceable?",
        [clause],
        client=FakeClient(),
    )
    assert answer["answer_status"] == "partially_answered"
    assert answer["stated_in_document"][0]["quote"] == clause.text
    assert "local law" in " ".join(answer["uncertainty_notes"]).lower()
    assert "lawyer" in answer["escalation"].lower()


def test_document_and_question_canaries_are_not_written_to_logs(caplog):
    clause = Clause(
        id="p1-c001",
        page=1,
        heading="Payment",
        text="Private canary clause text says rent is due each month.",
    )
    question = "Question canary: how much rent is due?"
    with caplog.at_level(logging.INFO, logger="legal_triage.citations"):
        structured_answer_question(question, [clause], client=FakeClient())
    assert "Private canary clause text" not in caplog.text
    assert question not in caplog.text
