# Private Legal Triage (frontend)

React + Vite frontend for the Private Legal Document Triage Agent. It uploads a PDF/TXT
to the team's local Python backend (Gemma on-device) and shows the summary, clauses,
concerns and the exact supporting passages. It ships with a clearly labelled demo mode
so it works before the backend is ready.

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

## Demo mode vs. real backend

- **Demo data**: returns `src/data/mockAnalysis.js` after a short delay. The file is not
  read or uploaded. Every demo result shows a "Demonstration data" banner.
- **Local backend**: creates a session with `POST /api/sessions`, polls its status, then reads the completed result. Cancelling or timing out deletes the session.

Switch with the "Data source" control in the upload panel. The starting mode comes from
`VITE_USE_MOCK` (`false` by default). Set it to `true` to start in demo mode.

## Pointing at the backend

```bash
cp .env.example .env.local   # then edit; restart npm run dev
```

| Variable | Default | Purpose |
| --- | --- | --- |
| `VITE_USE_MOCK` | `false` | Start in demo mode (`true`) or use the local backend (`false`) |
| `VITE_BACKEND_PROXY_TARGET` | `http://localhost:8000` | Where `npm run dev`/`preview` proxy `/api` |
| `VITE_API_BASE_URL` | empty | Call the backend directly instead (needs CORS on the backend) |
| `VITE_API_TIMEOUT_MS` | `600000` | Maximum analysis duration, including background processing |
| `VITE_API_POLL_INTERVAL_MS` | `1000` | Delay between session status checks |
| `VITE_MAX_FILE_MB` | `25` | Client-side upload size limit, matching the backend |

Easiest setup: leave `VITE_API_BASE_URL` empty and run the backend on port 8000. The dev
server proxies `/api/*` there, so no CORS configuration is needed.

## Backend contract

The frontend sends multipart form data with field `file` to `POST /api/sessions`, polls `GET /api/sessions/{id}/status`, and fetches `GET /api/sessions/{id}` when complete. The backend also exposes question and session deletion endpoints.

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
- The backend does not report confidence, so the UI labels it "unrated".
- `page` may be `null`; the UI shows "Page not provided".
- Errors: FastAPI-style `{"detail": "..."}` (or `error`/`message`) is shown to the user.

## Structure

```
src/
  App.jsx, App.css, main.jsx, config.js
  components/   Header, PrivacyBadge, UploadPanel, ModeSwitch, LoadingState, ErrorMessage,
                EmptyState, AnalysisDashboard, SummaryCards, ClauseList, EvidencePanel,
                ClauseTags, ConfidenceLabel, VerificationLabel, StatusPill, AboutSection
  hooks/        useAnalysis.js (request lifecycle, cancel)
  services/     api.js (fetch, timeout, validation, mock mode)
  data/         mockAnalysis.js (demo data only)
  utils/        fileValidation.js, clauseTags.js, format.js
```
