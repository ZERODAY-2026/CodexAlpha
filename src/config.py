"""
src/config.py — single source of truth for all runtime settings.
No secrets, no cloud endpoints.
"""
import os
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "false")
os.environ.setdefault("NO_UPDATE_NOTIFIER", "1")

HOST: str = os.getenv("HOST", "127.0.0.1")
PORT: int = int(os.getenv("PORT", "8000"))
SESSION_TTL_SECONDS: int = int(os.getenv("SESSION_TTL_SECONDS", "3600"))
MAX_UPLOAD_BYTES: int = int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))

# ---------------------------------------------------------------------------
# Ollama / LLM
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma4:e2b")
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_TIMEOUT_SECONDS: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "120"))

# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------
BM25_TOP_K: int = int(os.getenv("BM25_TOP_K", "5"))
STATUTE_SUBSET_PATH: Path = Path(
    os.getenv(
        "STATUTE_SUBSET_PATH",
        str(Path(__file__).resolve().parent.parent / "data" / "statutes" / "statute_subset.jsonl"),
    )
)

# ---------------------------------------------------------------------------
# Segmentation
# ---------------------------------------------------------------------------
# Minimum characters for a chunk to be kept (avoids blank/header-only chunks)
MIN_CHUNK_CHARS: int = 40
# Fallback paragraph chunk size (characters) when no heading pattern found
FALLBACK_CHUNK_SIZE: int = 800
FALLBACK_CHUNK_OVERLAP: int = 100

# ---------------------------------------------------------------------------
# Supported upload extensions
# ---------------------------------------------------------------------------
SUPPORTED_EXTENSIONS: tuple[str, ...] = (".pdf", ".txt")

# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
APP_TITLE: str = "Legal Document Triage Agent"
DISCLAIMER: str = (
    "⚠️ This is automated triage output, not legal advice. "
    "Consult a qualified solicitor before acting on any finding."
)
