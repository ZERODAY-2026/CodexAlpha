import logging

from src.analyze import (
    _detect_categories,
    _generate_summary,
    analyse_document,
    answer_question,
    structured_answer_question,
)
from src.segment import Clause, SegmentedDocument


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


def test_document_analysis_batches_category_matched_clauses():
    clauses = [
        Clause(
            id=f"p1-c{index:03}",
            page=1,
            heading="Payment",
            text=f"Clause {index}: The tenant shall pay rent on day {index} each month.",
        )
        for index in range(1, 9)
    ]

    class BatchClient:
        def __init__(self):
            self.prompts = []

        def generate_json(self, prompt: str):
            self.prompts.append(prompt)
            if '"claims"' in prompt:
                return {"claims": []}
            analyses = []
            for clause in clauses:
                if f"Clause id: {clause.id} |" in prompt:
                    analyses.append({
                        "clause_id": clause.id,
                        "category": _detect_categories(clause.text)[0],
                        "quote": clause.text,
                        "plain_explanation": "The tenant pays rent monthly.",
                        "possible_concern": "The clause does not specify the payment due date.",
                        "suggested_revision": "The tenant shall pay rent by [agreed due date] each month.",
                    })
            return {"analyses": analyses}

    client = BatchClient()
    progress = []
    result = analyse_document(
        SegmentedDocument(source_name="agreement.txt", clauses=clauses),
        client=client,
        progress_callback=lambda done, total, stage: progress.append((done, total, stage)),
    )

    assert len(client.prompts) == 3  # One summary call plus two batches of four clauses.
    assert len(result.key_clauses) == len(clauses)
    assert len({item.clause_id for item in result.key_clauses}) == len(clauses)
    assert result.key_clauses[0].suggested_revision == (
        "The tenant shall pay rent by [agreed due date] each month."
    )
    assert progress[-1] == (3, 3, "Analysing clauses")


def test_document_analysis_retries_missing_wording_for_a_concern():
    clause = Clause(
        id="p1-c001",
        page=1,
        heading="Payment",
        text="The tenant shall pay rent when requested by the landlord.",
    )

    class ConcernClient:
        def __init__(self):
            self.prompts = []

        def generate_json(self, prompt: str):
            self.prompts.append(prompt)
            if '"claims"' in prompt:
                return {"claims": []}
            if '"analyses"' in prompt:
                return {
                    "analyses": [{
                        "clause_id": clause.id,
                        "category": "obligation",
                        "quote": clause.text,
                        "plain_explanation": "The tenant must pay rent when asked.",
                        "possible_concern": "The clause does not specify when payment is due.",
                        "suggested_revision": None,
                    }]
                }
            assert '"revisions"' in prompt
            assert "The clause does not specify when payment is due." in prompt
            return {
                "revisions": [{
                    "clause_id": clause.id,
                    "quote": clause.text,
                    "suggested_revision": (
                        "The tenant shall pay rent within [number of days] after "
                        "receiving the landlord's written request."
                    ),
                }]
            }

    client = ConcernClient()
    result = analyse_document(
        SegmentedDocument(source_name="agreement.txt", clauses=[clause]),
        client=client,
    )

    assert len(client.prompts) == 3
    assert len(result.key_clauses) == 1
    assert result.key_clauses[0].possible_concern
    assert result.key_clauses[0].suggested_revision == (
        "The tenant shall pay rent within [number of days] after "
        "receiving the landlord's written request."
    )


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


def test_summary_returns_short_conversational_paragraph_from_verified_claims():
    clause = Clause(
        id="p1-c001",
        page=1,
        heading="Payment",
        text="Tenant shall pay rent on the first day of every month. Late fee is $10.",
    )

    class SummaryClient:
        def generate_json(self, prompt: str):
            assert "at most 60 words and three sentences" in prompt
            assert "a clause-by-clause list" in prompt
            return {
                "claims": [
                    {
                        "claim": "This agreement requires the tenant to pay rent on the first day of each month.",
                        "quote": "Tenant shall pay rent on the first day of every month.",
                        "clause_id": "p1-c001",
                    },
                    {
                        "claim": "Late payments incur a $10 fee.",
                        "quote": "Late fee is $10.",
                        "clause_id": "p1-c001",
                    },
                ]
            }

    summary = _generate_summary([clause], SummaryClient(), [])
    assert "\n" not in summary
    assert summary.startswith("This agreement requires the tenant to pay rent")
    assert "Late payments incur a $10 fee." in summary
    assert "“" not in summary
    assert "(p1-c001" not in summary


def test_summary_fallback_is_a_single_concise_paragraph():
    clause = Clause(
        id="p1-c001",
        page=1,
        heading="Payment",
        text="  The tenant shall pay rent monthly.  ",
    )

    class EmptySummaryClient:
        def generate_json(self, _prompt: str):
            return {"claims": []}

    summary = _generate_summary([clause], EmptySummaryClient(), [])

    assert summary == "The tenant shall pay rent monthly."
    assert "\n" not in summary


def test_summary_enforces_sentence_and_word_limits():
    clause = Clause(
        id="p1-c001",
        page=1,
        heading="Payment",
        text="The tenant shall pay rent monthly.",
    )

    class VerboseSummaryClient:
        def generate_json(self, _prompt: str):
            return {
                "claims": [
                    {
                        "claim": " ".join(["The agreement requires payment"] * 30) + ".",
                        "quote": "The tenant shall pay rent monthly.",
                        "clause_id": "p1-c001",
                    },
                ]
            }

    summary = _generate_summary([clause], VerboseSummaryClient(), [])

    assert len(summary.split()) <= 60
    assert len(summary.splitlines()) == 1
    assert summary.endswith("…")


def test_statutory_background_is_passed_as_separate_reference_context():
    clause = Clause(
        id="p1-c001",
        page=1,
        heading="Payment",
        text="The tenant shall pay rent each month.",
    )

    class PromptClient(FakeClient):
        prompt = ""

        def generate_json(self, prompt: str):
            self.prompt = prompt
            return super().generate_json(prompt)

    client = PromptClient()
    structured_answer_question(
        "What does the tenant have to do?",
        [clause],
        client=client,
        statutory_background=[
            {
                "act_title": "Example Act",
                "state": "central",
                "year": 2020,
                "section_number": "12",
                "excerpt": "A sample statutory excerpt.",
            }
        ],
    )
    assert "Optional statutory background (may be empty; not evidence about the agreement)" in client.prompt
    assert "Example Act" in client.prompt
    assert "A sample statutory excerpt." in client.prompt


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
