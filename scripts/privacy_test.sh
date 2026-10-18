#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODEL="${OLLAMA_MODEL:-gemma4:e2b}"
IMAGE="${PRIVACY_TEST_IMAGE:-local-legal-triage-privacy-test}"
OLLAMA_STORE="${OLLAMA_MODELS_DIR:-$HOME/.ollama}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required to isolate both the API and Ollama with --network none." >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "Docker is installed but its daemon is not running. Start Docker Desktop, then retry." >&2
  exit 1
fi
if [ ! -d "$OLLAMA_STORE/models" ]; then
  echo "No local Ollama model store found at $OLLAMA_STORE. Set OLLAMA_MODELS_DIR to it." >&2
  exit 1
fi

docker build -f "$ROOT/scripts/privacy.Dockerfile" -t "$IMAGE" "$ROOT"
docker run --rm --network none \
  -e "OLLAMA_MODEL=$MODEL" \
  -e "OLLAMA_HOST=127.0.0.1:11434" \
  -v "$OLLAMA_STORE:/root/.ollama:rw" \
  "$IMAGE"
