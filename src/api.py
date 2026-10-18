from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

try:
    from src.analyze import REFUSAL_PATTERN, analyse_document, structured_answer_question
    from src.config import APP_TITLE, MAX_UPLOAD_BYTES
    from src.guard import scan_prompt_injection
    from src.ingest import load_document
    from src.jurisdiction_warnings import detect_jurisdiction_warnings, infer_document_type
    from src.statutes import enrich_jurisdiction_warnings
    from src.llm import OllamaClient
    from src.retrieve import ClauseRetriever, RetrievalResult
    from src.segment import segment_document
    from src.session import SessionRecord, store
except ImportError:  # pragma: no cover
    from analyze import REFUSAL_PATTERN, analyse_document, structured_answer_question
    from config import APP_TITLE, MAX_UPLOAD_BYTES
    from guard import scan_prompt_injection
    from ingest import load_document
    from jurisdiction_warnings import detect_jurisdiction_warnings, infer_document_type
    from statutes import enrich_jurisdiction_warnings
    from llm import OllamaClient
    from retrieve import ClauseRetriever, RetrievalResult
    from segment import segment_document
    from session import SessionRecord, store

logger = logging.getLogger("legal_triage")
app = FastAPI(title=APP_TITLE, docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
GENERAL_REVIEW_QUESTION = re.compile(
    r"\b(change|revise|amend|fix|improve|update|review|concern|issue|problem|"
    r"what should|what must|what needs|things to)\b",
    re.IGNORECASE,
)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


def _set_failed(record: SessionRecord, exc: Exception) -> None:
    if isinstance(exc, ValueError):
        message = str(exc)
        if (
            "extractable text" in message
            or "empty" in message
            or "malformed" in message
            or "tesseract" in message.lower()
        ):
            safe_message = message
        else:
            safe_message = "The uploaded file could not be read. Choose a valid PDF or text file."
    elif isinstance(exc, RuntimeError):
        safe_message = str(exc)
    else:
        safe_message = "Analysis failed. Check that Ollama is running and the selected model is available."
    record.status = {
        "stage": "failed",
        "done": 0,
        "total": record.status.get("total", 0),
        "error": safe_message,
    }


def _process_upload(record: SessionRecord, contents: bytes, filename: str) -> None:
    try:
        record.status = {"stage": "extracting", "done": 0, "total": 1}
        document = load_document(contents, filename=filename)
        segmented = segment_document(document)
        if not segmented.clauses:
            raise ValueError("No readable clauses were found. Try a text-based PDF or plain text file.")
        record.status = {"stage": "analysing", "done": 0, "total": len(segmented.clauses) + 1}

        def update_progress(done: int, total: int, stage: str) -> None:
            record.status = {"stage": stage, "done": done, "total": total}

        analysis = analyse_document(
            segmented,
            client=OllamaClient(),
            progress_callback=update_progress,
        )
        doc_type = infer_document_type(segmented.clauses)
        jurisdiction_warnings = enrich_jurisdiction_warnings(
            analysis.jurisdiction_warnings or detect_jurisdiction_warnings(segmented.clauses, doc_type),
            doc_type,
        )
        retriever = ClauseRetriever(segmented)
        record.summary = analysis.summary
        record.key_clauses = [
            {
                "clause_id": item.clause_id,
                "category": item.category,
                "quote": item.quote,
                "plain_explanation": item.plain_explanation,
                "possible_concern": item.possible_concern,
                "suggested_revision": item.suggested_revision,
                "verified": item.verified,
                "page": item.page,
                "quote_start": item.quote_start,
                "quote_end": item.quote_end,
            }
            for item in analysis.key_clauses
        ]
        record.source_clauses = [
            {
                "id": clause.id,
                "page": clause.page,
                "text": clause.text,
                "suspicious_patterns": scan_prompt_injection(clause.text),
            }
            for clause in segmented.clauses
        ]
        record.data = {
            "retriever": retriever,
            "risks": analysis.risks,
            "suspicious_text": analysis.suspicious_text,
            "warnings": analysis.warnings,
            "jurisdiction_warnings": jurisdiction_warnings,
            "doc_type": doc_type,
            "page_count": document.total_pages,
            "clause_count": len(segmented.clauses),
        }
        record.status = {
            "stage": "done",
            "done": len(segmented.clauses) + 1,
            "total": len(segmented.clauses) + 1,
        }
        logger.info(
            "analysis_complete clauses=%d pages=%d verified_key_clauses=%d",
            len(segmented.clauses),
            document.total_pages,
            len(record.key_clauses),
        )
    except Exception as exc:
        _set_failed(record, exc)
        logger.info("analysis_failed stage=%s", record.status["stage"])


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; connect-src 'self'; img-src 'self' data:; "
        "style-src 'self'; script-src 'self'; object-src 'none'; "
        "base-uri 'self'; frame-ancestors 'none'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/sessions", status_code=202)
async def create_session(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> dict[str, Any]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".txt"}:
        raise HTTPException(status_code=415, detail="Upload a PDF or plain-text .txt file.")
    contents = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is too large. The maximum upload size is 25 MB.")
    record = store.create(Path(file.filename or "document").name)
    record.status = {"stage": "queued", "done": 0, "total": 1}
    background_tasks.add_task(_process_upload, record, contents, Path(file.filename or "document").name)
    return {"id": record.session_id, "status": record.status}


@app.get("/api/sessions/{session_id}/status")
def get_status(session_id: str) -> dict[str, Any]:
    record = store.get(session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    return {"id": record.session_id, "status": record.status}


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    record = store.get(session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    return {
        "id": record.session_id,
        "document_name": record.document_name,
        "summary": record.summary,
        "status": record.status,
        "key_clauses": record.key_clauses,
        "source_clauses": record.source_clauses,
        "risks": record.data.get("risks", []),
        "suspicious_text": record.data.get("suspicious_text", []),
        "warnings": record.data.get("warnings", []),
        "jurisdiction_warnings": record.data.get("jurisdiction_warnings", []),
        "page_count": record.data.get("page_count", 0),
    }


@app.post("/api/sessions/{session_id}/ask")
def ask_question(session_id: str, payload: QuestionRequest) -> dict[str, Any]:
    record = store.get(session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    if record.status.get("stage") != "done":
        raise HTTPException(status_code=409, detail="Wait for document analysis to finish before asking a question.")

    retriever: ClauseRetriever | None = record.data.get("retriever")
    if retriever is None:
        raise HTTPException(status_code=410, detail="The in-memory document index is no longer available.")
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Enter a question.")
    retrieved = retriever.search(question)
    all_clauses = retriever.get_all_clauses()
    if REFUSAL_PATTERN.search(question) and not retrieved:
        retrieved = retriever.search(question, top_k=len(all_clauses)) or []
    if GENERAL_REVIEW_QUESTION.search(question) and all_clauses:
        prioritized_ids = [
            item.get("clause_id")
            for item in record.key_clauses
            if isinstance(item, dict)
        ]
        risks = record.data.get("risks", [])
        if isinstance(risks, list):
            prioritized_ids.extend(
                item.get("clause_id")
                for item in risks
                if isinstance(item, dict) and item.get("clause_id")
            )
        by_id = {clause.id: clause for clause in all_clauses}
        selected: list[RetrievalResult] = []
        seen_ids = set()
        for clause_id in prioritized_ids:
            clause = by_id.get(clause_id)
            if clause is not None and clause.id not in seen_ids:
                selected.append(RetrievalResult(clause=clause, score=0.0))
                seen_ids.add(clause.id)
        for result in retrieved:
            if result.clause.id not in seen_ids:
                selected.append(result.clause)
                seen_ids.add(result.clause.id)
        for clause in all_clauses:
            if clause.id not in seen_ids:
                selected.append(RetrievalResult(clause=clause, score=0.0))
                seen_ids.add(clause.id)
            if len(selected) >= 10:
                break
        retrieved = selected[:10]
    try:
        source_clauses = [item.clause for item in retrieved]
        warnings = record.data.get("jurisdiction_warnings", [])
        selected_ids = {clause.id for clause in source_clauses}
        relevant_warnings = [
            warning
            for warning in warnings
            if isinstance(warning, dict)
            and (
                not selected_ids
                or any(
                    isinstance(trigger, dict) and trigger.get("clause_id") in selected_ids
                    for trigger in warning.get("triggering_clauses", [])
                )
            )
        ]
        statute_background = []
        seen_sections = set()
        for warning in relevant_warnings:
            for section in warning.get("statutory_background", []):
                if not isinstance(section, dict):
                    continue
                key = (section.get("act_title"), section.get("section_number"), section.get("snapshot"))
                if key not in seen_sections:
                    statute_background.append(section)
                    seen_sections.add(key)
                if len(statute_background) >= 8:
                    break
            if len(statute_background) >= 8:
                break
        answer = structured_answer_question(
            question,
            source_clauses,
            OllamaClient(),
            statutory_background=statute_background,
        )
        answer["statutory_background_available"] = bool(statute_background)
        answer["jurisdiction_warnings"] = enrich_jurisdiction_warnings(
            relevant_warnings or detect_jurisdiction_warnings(
                source_clauses,
                record.data.get("doc_type", "both"),
            ),
            record.data.get("doc_type", "both"),
        )
        return answer
    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail="The local model could not complete a structured answer. Check the model status and retry.",
        ) from exc


@app.delete("/api/sessions/{session_id}", status_code=204, response_class=Response)
def delete_session(session_id: str) -> Response:
    if not store.delete(session_id):
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    return Response(status_code=204)


@app.get("/")
def index() -> FileResponse:
    index_file = FRONTEND_DIST / "index.html"
    if not index_file.is_file():
        raise HTTPException(status_code=503, detail="Frontend not built. Run npm ci and npm run build in frontend/.")
    return FileResponse(index_file)


@app.get("/{path:path}")
def frontend_files(path: str) -> FileResponse:
    requested_path = (FRONTEND_DIST / path).resolve()
    if FRONTEND_DIST.resolve() not in requested_path.parents and requested_path != FRONTEND_DIST.resolve():
        raise HTTPException(status_code=404, detail="Not found.")
    if requested_path.is_file():
        return FileResponse(requested_path)
    index_file = FRONTEND_DIST / "index.html"
    if index_file.is_file() and not path.startswith(("api/", "assets/")):
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="Not found.")
