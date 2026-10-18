# Architecture and local data flow

```text
Browser (React, same-origin; development Vite at 127.0.0.1:5173)
    │ upload / question / progress / results
    ▼
FastAPI + Uvicorn (127.0.0.1:8000)
    ├── PDF/TXT extraction (local Tesseract OCR fallback) → clauses → in-memory BM25 index
    ├── in-memory session data (expires after configured TTL)
    └── verified summary, clause and answer citations
          │ prompt + document data; loopback only
          ▼
      Ollama (127.0.0.1:11434; gemma4:e2b by default)
```

No cloud service is contacted for model inference, OCR, embedding, analytics, or document storage. PyMuPDF uses the locally installed Tesseract engine on image-containing PDF pages with little selectable text. The optional statute subset is a local, user-generated read-only runtime input. The browser sends API requests only to its own origin. In Vite development mode, Vite forwards `/api` and `/health` to the loopback FastAPI server; production uses the same-origin FastAPI static server. Uploaded bytes and extracted text are kept in memory and removed when the session expires or the user deletes it. See [NETWORK.md](./NETWORK.md) and [DATA.md](./DATA.md).

The document pipeline extracts selectable PDF page text, OCRing image-containing pages with little selectable text using local Tesseract, or decodes UTF-8 text files. It segments text into page-addressed clauses, ranks clauses using local BM25, and sends bounded document blocks to local Ollama. Analysis makes one summary request plus one request per batch of up to four relevant clauses; each clause is analyzed once under its most relevant detected category instead of making repeated calls for every matching category. Every model-supplied citation is verified against its source clause before returning it. Optional model-drafted wording suggestions are paired only with verified source passages and are displayed as proposals, not legal requirements. Separately, hard-coded rule IDs may retrieve fixed-mapping matches from the optional statute BM25 index; document text and questions are never inputs to that search. The browser displays statutory excerpts separately from document citations and model answers, and displays text as React text nodes rather than HTML.
