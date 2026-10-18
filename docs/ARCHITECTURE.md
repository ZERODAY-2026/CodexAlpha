# Architecture and local data flow

```text
Browser (React, same-origin; development Vite at 127.0.0.1:5173)
    │ upload / question / progress / results
    ▼
FastAPI + Uvicorn (127.0.0.1:8000)
    ├── PDF/TXT extraction → clauses → in-memory BM25 index
    ├── in-memory session data (expires after configured TTL)
    └── verified summary, clause and answer citations
          │ prompt + document data; loopback only
          ▼
      Ollama (127.0.0.1:11434; gemma4:e2b by default)
```

The app makes no cloud model, OCR, embedding, analytics, or storage calls. The browser sends API requests only to its own origin. In Vite development mode, Vite forwards `/api` and `/health` to the loopback FastAPI server; production uses the same-origin FastAPI static server. Uploaded bytes and extracted text are kept in memory and removed when the session expires or the user deletes it. See [NETWORK.md](./NETWORK.md).

The pipeline extracts PDF page text or UTF-8 text, segments it into page-addressed clauses, ranks clauses using local BM25, sends bounded document blocks to local Ollama, and verifies every model-supplied citation against its source clause before returning it. The browser displays document statements separately from interpretations and concerns, and displays document text as React text nodes rather than HTML.
