# Project Context — Private On-Device Legal Document Triage Agent
> ZeroDay OSS Hacktoberfest 2026 · Problem Statement 2

## Non-Negotiable Rules

Every contributor, every task, every AI prompt referencing this project **must** follow these rules without exception.

---

### Rule 1 — All Data Stays On-Device
All document content — uploaded files, extracted text, chunks, embeddings, summaries, answers, and user questions — **must never leave the local machine**.  
Prohibited: remote LLM APIs, cloud OCR, vector-database SaaS, telemetry, analytics, crash-reporting SDKs, or any log that contains document text.  
The only permitted external network call is to `127.0.0.1` (Ollama's local HTTP API).

### Rule 2 — Output Is Triage, Never Legal Advice
Every output is **preliminary document understanding only**.  
The system **must never** characterise a clause as "legal", "illegal", "valid", "invalid", "enforceable", or "unenforceable".  
All outputs must carry the disclaimer: *"This is automated triage output, not legal advice. Consult a qualified solicitor."*

### Rule 3 — Every Claim Must Cite a Verbatim Passage
Any factual statement about a document must be accompanied by a direct quote (the exact words) from that document, plus the page number and clause ID where the quote appears.  
If the document is silent on a topic, the output **must** say so explicitly: *"The document does not address this."*

### Rule 4 — Explicit Statements vs. Interpretations Are Visibly Separated
Two distinct visual zones must appear in every output section:
- **Document says** — verbatim or close-paraphrase of the text.
- **Possible concern / This could mean** — interpretive commentary, always clearly labelled.

Mixing the two zones is prohibited.

### Rule 5 — Document Text Is Untrusted Data, Never Instructions
Parsed document text is treated as data only, never as prompt directives.  
All LLM prompts must wrap document content in explicit delimiters (e.g. `<document_text>…</document_text>`) and include an instruction to ignore any instructions embedded in the content.

---

## Scope
| Document type | Format |
|---|---|
| Rental agreements | PDF, plain text (`.txt`) |
| Employment agreements | PDF, plain text (`.txt`) |

Other document types may be loaded but will receive a best-effort analysis with no guarantees.

---

## Architecture Overview

```
uploaded file
     │
     ▼
 src/ingest.py   ← extract text per page (PyMuPDF / plain-text reader)
     │
     ▼
 src/segment.py  ← split into clause/section chunks with id + page
     │
     ▼
 src/retrieve.py ← BM25 keyword search over clauses (rank_bm25)
     │
     ▼
 src/llm.py      ← thin HTTP client → Ollama @ 127.0.0.1 (JSON output)
     │
     ▼
 src/analyze.py  ← summary + per-clause analysis (obligations, rights, …)
     │
     ▼
 src/api.py      ← FastAPI, in-memory sessions, status, Q&A, static frontend
     │
     ▼
 frontend/       ← React/Vite app served by FastAPI after a one-time build
```

Configuration lives exclusively in `src/config.py`.

---

## Stack
| Concern | Library / Tool |
|---|---|
| PDF parsing | PyMuPDF (`fitz`) |
| Retrieval | `rank_bm25` |
| Local LLM | Ollama HTTP API (`gemma4:e2b` by default) |
| API / server | FastAPI + Uvicorn, bound to `127.0.0.1` |
| UI | React + Vite, served from `frontend/dist` |
| Python | 3.11 |

The default Ollama tag is `gemma4:e2b`, and can be overridden with `OLLAMA_MODEL`.
Ollama is contacted only at a loopback address. Configure Ollama itself to listen
on `127.0.0.1:11434`.

---

## What This Project Is Not
- It is **not** a legal research tool.
- It is **not** a document signing or storage service.
- It is **not** connected to the internet during normal operation.
