# Private Legal Triage (frontend)

React + Vite frontend for the Private Legal Document Triage Agent. It uploads a PDF/TXT
to the team's local Python backend (Gemma on-device) and shows the summary, clauses,
concerns, supporting passages, and a document Q&A chat.

## Run

```bash
npm install
npm run dev          # http://localhost:5173
```

Production build check:

```bash
npm run build
npm run preview      # http://localhost:4173 (also proxies /api)
```

Requires Node 20.19+ (tested on Node 22).

## Pointing at the backend

```bash
cp .env.example .env.local   # then edit; restart npm run dev
```

| Variable | Default | Purpose |
| --- | --- | --- |
| `VITE_BACKEND_PROXY_TARGET` | `http://localhost:8000` | Where `npm run dev`/`preview` proxy `/api` |
| `VITE_API_BASE_URL` | empty | Call the backend directly instead (needs CORS on the backend) |
| `VITE_API_TIMEOUT_MS` | `600000` | Maximum analysis duration, including background processing |
| `VITE_API_POLL_INTERVAL_MS` | `1000` | Delay between session status checks |
| `VITE_MAX_FILE_MB` | `25` | Client-side upload size limit, matching the backend |

Easiest setup: leave `VITE_API_BASE_URL` empty and run the backend on port 8000. The dev
server proxies `/api/*` there, so no CORS configuration is needed.

## Backend contract

The frontend sends multipart form data with field `file` to `POST /api/sessions`, polls `GET /api/sessions/{id}/status`, and fetches `GET /api/sessions/{id}` when complete. After analysis, the chat sends questions to `POST /api/sessions/{id}/ask`. Use **Delete document and start over** to delete the in-memory session.

```json
{
  "id": "session-id",
  "document_name": "agreement.pdf",
  "summary": "Summary based on extracted document text.",
  "key_clauses": [
    {
      "clause_id": "p1-c001",
      "category": "Termination",
      "page": 2,
      "quote": "Exact passage from the source document.",
      "plain_explanation": "What the clause states.",
      "possible_concern": "A possible ambiguity to review.",
      "verified": true
    }
  ],
  "warnings": []
}
```

How the frontend treats the result (`src/services/api.js`):

- `key_clauses` must be an array, otherwise the response is rejected as invalid.
- `verified` counts only if it is exactly `true`; anything else shows "Unverified quote".
- `page` may be `null`; the UI shows "Page not provided".
- Chat answers display only passages that the backend marks as verified.
- Errors: FastAPI-style `{"detail": "..."}` (or `error`/`message`) is shown to the user.

## Structure

```
src/
  App.jsx, App.css, main.jsx, config.js
  components/   Header, UploadPanel, LoadingState, ErrorMessage, EmptyState,
                AnalysisDashboard, SummaryCards, ClauseList, EvidencePanel, ChatPanel,
                VerificationLabel, StatusPill
  hooks/        useAnalysis.js (request lifecycle, cancel)
  services/     api.js (backend requests and response validation)
  utils/        fileValidation.js, format.js
```
