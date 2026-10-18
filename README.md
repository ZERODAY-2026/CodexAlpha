# CODEXALPHA - Private Legal Document Triage

A local-first assistant for preliminary understanding of rental and employment agreements in PDF or plain-text format. Uploaded document data and questions stay in process memory, and model requests go only to Ollama on loopback. An optional, manually built local subset can show statutory background alongside generic jurisdiction warnings.

> **Preliminary understanding, not legal advice.** The app does not decide legal status, predict case outcomes, or advise whether to sign. Ask a qualified local professional about important decisions.

## Requirements

- Python 3.11
- Node.js and npm for the one-time frontend build
- Ollama installed locally with the model tag shown by `ollama list` (default: `gemma4:e2b`)
- Tesseract OCR with English language data for scanned PDFs (`brew install tesseract` on macOS, or `sudo apt install tesseract-ocr` on Debian/Ubuntu)

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

Open `http://127.0.0.1:8000/`. Upload a PDF or `.txt` agreement. Analysis runs in the background; progress is polled locally. Review the summary, key clauses, and source passages, then chat with the document using cited answers. **Delete document and start over** removes the in-memory session.

PDFs with selectable text are extracted directly. Pages that contain images but little selectable text are OCRed locally with Tesseract; English is used by default. If the app cannot locate Tesseract's English data, set `TESSDATA_PREFIX` to the directory containing `eng.traineddata` before starting FastAPI.

For development, keep the backend running and launch Vite from `frontend/`:

```bash
cd frontend
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
| `STATUTE_SUBSET_PATH` | `data/statutes/statute_subset.jsonl` | Optional local statutory background subset; missing files disable this feature |

## Optional statutory background

Statutory background is off unless you build the local subset. The subset builder makes a setup-time request to Hugging Face for the `legislation` configuration of [Open India Law](https://huggingface.co/datasets/vaquill/open-india-law). It streams rows and writes only selected sections under the git-ignored `data/statutes/` directory. The app never downloads the dataset. At runtime, statute retrieval is local BM25; document text and questions are not used for statute search.

To enable it:

1. Install the setup-only packages: `python -m pip install -r requirements-setup.txt`.
2. Sign in with `huggingface-cli login`, or set `HF_TOKEN` in your environment without printing it or saving it in the repository.
3. Visit the dataset page, sign in, and accept its access conditions.
4. Review and customize `config/statute_acts.json`, especially `exact_titles` for ambiguous title matches. The starter list is only a suggestion.
5. Run `python -m scripts.build_statute_subset` from the repository root. Review the reported matches and `data/statutes/ATTRIBUTION.md`.
6. Restart FastAPI. The optional excerpts and snapshot label will appear only when the local subset loads successfully.

The download and subset build are setup-time network activity. The app does not fetch or update statutes while running. See [docs/NETWORK.md](docs/NETWORK.md), [docs/DATA.md](docs/DATA.md), and [docs/LIMITATIONS.md](docs/LIMITATIONS.md).

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
- **Scanned PDF OCR is unavailable:** install Tesseract and its English language data, then restart FastAPI. If the language data is installed in a non-standard location, set `TESSDATA_PREFIX` to the directory containing `eng.traineddata`. Confirm the install with `tesseract --list-langs`.
- **Frontend not built:** run `npm ci && npm run build` in `frontend/`.
- **Browser page is blank:** check the backend terminal and open the browser console. The API is same-origin and should be accessed at `127.0.0.1:8000`.

## Privacy and scope

Model inference and OCR run locally. No cloud OCR, embedding, analytics, telemetry, or document-storage service is contacted at runtime. See [docs/NETWORK.md](docs/NETWORK.md) for setup-time network calls and runtime boundaries. This prototype focuses on rental and employment agreements and should not be treated as complete document review.

When matching clause text is found, the app may show a fixed, generic jurisdiction background warning. These keyword-based notices are separate from document analysis and citations; they do not identify applicable law or describe a clause's status. See [docs/LIMITATIONS.md](docs/LIMITATIONS.md).

The provided sample agreements are fictional and self-written. Upload [rental_agreement_sample.pdf](sample_docs/rental_agreement_sample.pdf) in the browser UI to test PDF extraction; recreate it with `python -m scripts.generate_sample_pdf`. See [docs/LIMITATIONS.md](docs/LIMITATIONS.md) and [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md).
