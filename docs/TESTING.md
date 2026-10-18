# Testing

Run the deterministic suite with:

```bash
python -m pytest -q
cd frontend
npm test
npm run build
```

Tests cover malformed/empty files, quote matching and offsets, dropping fabricated citations, document-silent answers, enforceability-question refusal, prompt-injection detection, review flags, and metadata-only logs. Synthetic offline fixtures cover the optional statute loader and setup builder; the tests never download dataset rows. Vitest checks citation guards and the optional statutory background panel.

For a runtime-only network-isolated end-to-end check, prepare the Docker image and model store, then run `bash scripts/privacy_test.sh`. The script starts the API and Ollama in the same container under `--network none`, analyzes a fictional sample, asks a question, verifies the API citation gate, and deletes the session. The test needs Docker and the selected Ollama model already present in the mounted local model store.

The benchmark script (`python -m scripts.benchmark`) uses synthetic prompts and writes device-specific results to [BENCHMARKS.md](./BENCHMARKS.md). Never treat results from a different machine as representative.

## Current verification

Verified on macOS 26.5.2 / arm64 with Python 3.12 (the documented minimum target, Python 3.11, was not installed for this run) and the local Ollama tag `gemma4:e2b`:

- Backend: `23 passed` (`python -m pytest -q`).
- Frontend: `2 passed` (`npm test`).
- TypeScript: `tsc --noEmit` completed without diagnostics.
- Production frontend: `npm run build` succeeded.
- Live local model check: uploaded both fictional rental samples, including `rental_agreement_sample.pdf` through the React UI. PDF analysis rendered a cited overview and six key clauses; asking “When is rent due?” returned a verified citation, selecting it highlighted the matching source text, and deleting the session returned the UI to its upload state. Text-upload checks also passed for document-silent responses, enforceability refusal, and session deletion.
- Network audit: no `https://` URLs in the built bundle. The built React runtime contains only W3C namespace identifiers (`http://www.w3.org/...`), not remote assets or calls. Source call sites are relative browser `fetch` and the loopback-validated Ollama HTTP client.
- Offline Docker test: **blocked by model/runtime incompatibility**. The `--network none` container starts both services and can see the mounted `gemma4:e2b` tag, but generation fails because this local model requires Ollama's MLX runtime, which is not available in the Linux container (`MLX runtime is not available`). The harness disables Ollama cloud features, and the captured attempts are in [docs/evidence/privacy_test.log](./evidence/privacy_test.log). The same installed model passed the live analysis/Q&A flow through native macOS Ollama; the Docker-only model execution check remains unmet.

Pytest reports two upstream deprecation warnings from the pinned FastAPI/Starlette test stack; they do not fail the suite.
