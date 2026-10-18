# Network policy and audit

## Runtime

The app's permitted runtime network request is the backend's HTTP POST to Ollama at `127.0.0.1:11434`. `src/llm.py` validates every configured Ollama URL and rejects non-loopback destinations. Uvicorn and Vite are configured to bind to `127.0.0.1`. In development, Vite proxies only `/api` and `/health` to the local FastAPI server, so the browser talks only to its own origin. FastAPI serves the built app from the same origin in production. Generic jurisdiction warnings are produced locally from hard-coded rules. Optional statutory background is read from `STATUTE_SUBSET_PATH` and searched with local BM25; it makes no runtime network calls and sends no document or question text to that index.

The Vite page and API responses use a restrictive Content Security Policy with `connect-src 'self'`; the frontend has no CDN, remote font, analytics, or remote image dependency. All application logs are metadata-only; Uvicorn access logs should be disabled using the README command.

## Setup-time calls

These calls are made only when a developer chooses to set up the project:

- `pip install -r requirements.txt` retrieves pinned packages from the configured Python package index.
- `npm ci` retrieves locked frontend packages from the configured npm registry.
- `ollama pull <tag>` retrieves model files through Ollama, if the model is not already installed.
- `python -m pip install -r requirements-setup.txt` retrieves setup-only dataset packages.
- After the user accepts the dataset's access conditions and signs in, `python -m scripts.build_statute_subset` streams only the Hugging Face `vaquill/open-india-law` `legislation` configuration and writes a curated local subset. This is a manual setup-time network call; it uses the user's Hugging Face login or `HF_TOKEN` and never stores a token in the repository.

After setup, the app does not invoke package managers, model downloads, or dataset downloads. It does not call the Hugging Face dataset at runtime. The dataset's Qdrant snapshots and Voyage embeddings are deliberately unused; statutory sections are retrieved only with the application's local BM25 implementation. Clicking a displayed source link is a user action that opens the linked source outside the app; the app does not fetch that page.

## Audit and offline check

Review app network call sites with:

```bash
rg -n 'requests\\.(get|post)|httpx\\.|urllib|fetch\\(|XMLHttpRequest|https?://' src frontend/src frontend/index.html
```

The one expected runtime client is the Ollama call in `src/llm.py`; other URLs should be setup-time documentation or the Vite loopback proxy. `scripts/privacy_test.sh` runs the app and Ollama together in a Docker container with `--network none`. Docker image construction and any missing package/model downloads must happen before that isolated run.
