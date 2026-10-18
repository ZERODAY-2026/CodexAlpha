# Network policy and audit

## Runtime

The app's permitted runtime network request is the backend's HTTP POST to Ollama at `127.0.0.1:11434`. `src/llm.py` validates every configured Ollama URL and rejects non-loopback destinations. Uvicorn and Vite are configured to bind to `127.0.0.1`. In development, Vite proxies only `/api` and `/health` to the local FastAPI server, so the browser talks only to its own origin. FastAPI serves the built app from the same origin in production.

The Vite page and API responses use a restrictive Content Security Policy with `connect-src 'self'`; the frontend has no CDN, remote font, analytics, or remote image dependency. All application logs are metadata-only; Uvicorn access logs should be disabled using the README command.

## Setup-time calls

These calls are made only when a developer chooses to set up the project:

- `pip install -r requirements.txt` retrieves pinned packages from the configured Python package index.
- `npm ci` retrieves locked frontend packages from the configured npm registry.
- `ollama pull <tag>` retrieves model files through Ollama, if the model is not already installed.

After setup, the app does not invoke package managers or model downloads. It does not use remote APIs for OCR, embeddings, model inference, analytics, or storage.

## Audit and offline check

Review app network call sites with:

```bash
rg -n 'requests\\.(get|post)|httpx\\.|urllib|fetch\\(|XMLHttpRequest|https?://' src frontend2/src frontend2/index.html
```

The one expected runtime client is the Ollama call in `src/llm.py`; other URLs should be setup-time documentation or the Vite loopback proxy. `scripts/privacy_test.sh` runs the app and Ollama together in a Docker container with `--network none`. Docker image construction and any missing package/model downloads must happen before that isolated run.
