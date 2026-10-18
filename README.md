# Private Legal Document Triage

A local-first assistant for preliminary understanding of rental and employment agreements in PDF or plain-text format. Uploaded document data and questions stay in process memory, and model requests go only to Ollama on loopback.

> **Preliminary understanding, not legal advice.** The app does not decide legal status, predict case outcomes, or advise whether to sign. Ask a qualified local professional about important decisions.

## Requirements

- Python 3.11
- Node.js and npm for the one-time frontend build
- Ollama installed locally with the model tag shown by `ollama list` (default: `gemma4:e2b`)

## Setup

From the repository root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
ollama list
```

If needed, download the model once while online:

```bash
ollama pull gemma4:e2b
```

For an already-downloaded model, skip `ollama pull`. The configured model must exactly match a tag printed by `ollama list`.

Build the browser app once:

```bash
cd frontend
npm ci
npm run build
cd ..
```

The compiled app is served by FastAPI; Node is not needed when running the built app.

## Run

If Ollama is not already running, start it in one terminal, restricted to loopback:

```bash
OLLAMA_HOST=127.0.0.1:11434 ollama serve
```

If the Ollama app is already running, do not start a second server; verify the model with `ollama list`. Then, from the repository root:

```bash
source .venv/bin/activate
OLLAMA_MODEL=gemma4:e2b python -m uvicorn src.api:app \
  --host 127.0.0.1 --port 8000 --no-access-log
```

Open `http://127.0.0.1:8000/`. Upload a PDF or `.txt` agreement. Analysis runs in the background; progress is polled locally. Ask document-grounded questions, select a verified citation to highlight its source passage, and use **Delete session data** to remove the in-memory session.

For development, keep the backend running and launch Vite from `frontend/`:

```bash
npm run dev
```

Open `http://127.0.0.1:5173/`. Vite proxies only `/api` and `/health` to `127.0.0.1:8000`.

## Configuration

Settings are in `src/config.py` and can be set with environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Local Ollama API; non-loopback hosts are rejected |
| `OLLAMA_MODEL` | `gemma4:e2b` | Must match an installed Ollama model tag |
| `LLM_TEMPERATURE` | `0.1` | Generation temperature |
| `LLM_TIMEOUT_SECONDS` | `120` | Local model request timeout |
| `BM25_TOP_K` | `5` | Number of source clauses considered per question |
| `SESSION_TTL_SECONDS` | `3600` | In-memory session lifetime |
| `MAX_UPLOAD_BYTES` | `26214400` | Maximum uploaded file size |

## Test

```bash
source .venv/bin/activate
python -m pytest -q
cd frontend
npm test
npm run build
```

## Troubleshooting

- **Cannot reach local Ollama:** ensure `ollama serve` is running and `OLLAMA_HOST` is `127.0.0.1:11434`.
- **Model not found:** run `ollama list` and set `OLLAMA_MODEL` to the exact listed tag. Download with `ollama pull <tag>` if needed.
- **Model response is slow:** increase `LLM_TIMEOUT_SECONDS` in the environment or use a smaller model already installed locally.
- **Scanned PDF or no extracted text:** the current parser requires selectable text. Export a text-based PDF or use a `.txt` copy; OCR is not included.
- **Frontend not built:** run `npm ci && npm run build` in `frontend/`.
- **Browser page is blank:** check the backend terminal and open the browser console. The API is same-origin and should be accessed at `127.0.0.1:8000`.

## Privacy and scope

No cloud model, OCR, embedding, storage, analytics, or telemetry integration is used at runtime. See [docs/NETWORK.md](docs/NETWORK.md) for setup-time network calls and runtime boundaries. This prototype focuses on rental and employment agreements and should not be treated as complete document review.

The provided sample agreements are fictional and self-written. Upload [rental_agreement_sample.pdf](sample_docs/rental_agreement_sample.pdf) in the browser UI to test PDF extraction; recreate it with `python -m scripts.generate_sample_pdf`. See [docs/LIMITATIONS.md](docs/LIMITATIONS.md) and [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md).
