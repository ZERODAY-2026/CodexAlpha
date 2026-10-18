#!/usr/bin/env bash
set -euo pipefail

export OLLAMA_HOST=127.0.0.1:11434
export OLLAMA_NO_CLOUD=true
ollama serve &
OLLAMA_PID=$!
API_PID=""
cleanup() {
  if [ -n "$API_PID" ]; then
    kill "$API_PID" 2>/dev/null || true
  fi
  kill "$OLLAMA_PID" 2>/dev/null || true
}
trap cleanup EXIT

python3 - <<'PY'
import os
import time
import requests

base = "http://127.0.0.1:11434"
for _ in range(120):
    try:
        tags = requests.get(f"{base}/api/tags", timeout=2).json()
        models = {item.get("name") for item in tags.get("models", [])}
        requested = os.environ["OLLAMA_MODEL"]
        if requested not in models:
            raise SystemExit(f"Required model {requested!r} is not present in the mounted local model store.")
        break
    except requests.RequestException:
        time.sleep(1)
else:
    raise SystemExit("Ollama did not start inside the offline container.")
PY

uvicorn src.api:app --host 127.0.0.1 --port 8000 --no-access-log &
API_PID=$!
python3 - <<'PY'
import time
import requests

for _ in range(60):
    try:
        if requests.get("http://127.0.0.1:8000/health", timeout=2).status_code == 200:
            break
    except requests.RequestException:
        time.sleep(1)
else:
    raise SystemExit("The API did not start inside the offline container.")

base = "http://127.0.0.1:8000"
with open("sample_docs/rental_agreement_sample.txt", "rb") as document:
    created = requests.post(
        f"{base}/api/sessions",
        files={"file": ("rental_agreement_sample.txt", document, "text/plain")},
        timeout=20,
    )
created.raise_for_status()
session_id = created.json()["id"]
for _ in range(600):
    status = requests.get(f"{base}/api/sessions/{session_id}/status", timeout=5).json()["status"]
    if status["stage"] == "done":
        break
    if status["stage"] == "failed":
        raise SystemExit(f"Analysis failed offline: {status.get('error', 'unknown error')}")
    time.sleep(1)
else:
    raise SystemExit("Offline analysis did not complete before timeout.")

answer = requests.post(
    f"{base}/api/sessions/{session_id}/ask",
    json={"question": "When is rent due?"},
    timeout=120,
)
answer.raise_for_status()
payload = answer.json()
for group in ("stated_in_document", "possible_interpretations", "concerns"):
    for item in payload[group]:
        if item.get("verified") is not True or not item.get("quote"):
            raise SystemExit("An unverified citation reached the offline API response.")
requests.delete(f"{base}/api/sessions/{session_id}", timeout=5).raise_for_status()
print("PASS: analysis, cited question answering, and session deletion succeeded with Docker networking disabled.")
PY
