from fastapi.testclient import TestClient

from src import api
from src.analyze import DocumentAnalysis


class FakeClient:
    def generate_json(self, prompt: str):
        return {
            "answer_status": "answered",
            "stated_in_document": [
                {
                    "claim": "Rent is due on the first day each month.",
                    "quote": "The tenant shall pay rent on the first day of each month.",
                    "clause_id": "p1-c001",
                }
            ],
            "possible_interpretations": [],
            "concerns": [],
            "uncertainty_notes": [],
            "escalation": "",
        }


def test_upload_status_question_delete_and_security_headers(monkeypatch):
    monkeypatch.setattr(api, "OllamaClient", FakeClient)
    monkeypatch.setattr(
        api,
        "analyse_document",
        lambda segmented, client, progress_callback: DocumentAnalysis(
            source_name=segmented.source_name,
            summary="Verified source passages are available below.",
        ),
    )
    contents = (
        b"1. Rent. The tenant shall pay rent on the first day of each month."
    )
    with TestClient(api.app) as client:
        response = client.post(
            "/api/sessions",
            files={"file": ("agreement.txt", contents, "text/plain")},
        )
        assert response.status_code == 202
        session_id = response.json()["id"]

        status = client.get(f"/api/sessions/{session_id}/status")
        assert status.json()["status"]["stage"] == "done"

        data = client.get(f"/api/sessions/{session_id}")
        assert data.status_code == 200
        assert data.json()["source_clauses"]
        assert data.json()["jurisdiction_warnings"] == []

        answer = client.post(
            f"/api/sessions/{session_id}/ask",
            json={"question": "When is rent due?"},
        )
        assert answer.status_code == 200
        assert answer.json()["stated_in_document"][0]["verified"] is True
        assert answer.json()["jurisdiction_warnings"] == []

        assert client.delete(f"/api/sessions/{session_id}").status_code == 204
        assert client.get(f"/api/sessions/{session_id}").status_code == 404

        health = client.get("/health")
        assert health.headers["content-security-policy"].startswith("default-src 'self'")


def test_upload_rejects_unsupported_file_types():
    with TestClient(api.app) as client:
        response = client.post(
            "/api/sessions",
            files={"file": ("agreement.docx", b"not supported", "application/octet-stream")},
        )
    assert response.status_code == 415


def test_analysis_and_retrieved_question_expose_matching_background_warnings(monkeypatch):
    monkeypatch.setattr(api, "OllamaClient", FakeClient)
    monkeypatch.setattr(
        api,
        "analyse_document",
        lambda segmented, client, progress_callback: DocumentAnalysis(
            source_name=segmented.source_name,
            summary="Verified source passages are available below.",
        ),
    )
    with TestClient(api.app) as client:
        created = client.post(
            "/api/sessions",
            files={
                "file": (
                    "rental.txt",
                    b"1. Security Deposit. The tenant pays a security deposit that is returned after the tenancy ends.",
                    "text/plain",
                )
            },
        )
        session_id = created.json()["id"]
        analyzed = client.get(f"/api/sessions/{session_id}").json()
        assert analyzed["jurisdiction_warnings"][0]["rule_id"] == "rental_security_deposit"

        answer = client.post(
            f"/api/sessions/{session_id}/ask",
            json={"question": "How is the security deposit handled?"},
        ).json()
        assert answer["jurisdiction_warnings"][0]["rule_id"] == "rental_security_deposit"
        assert answer["jurisdiction_warnings"][0]["triggering_clauses"][0]["clause_id"] == "p1-c001"
