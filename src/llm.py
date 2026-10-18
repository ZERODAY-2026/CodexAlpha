"""
src/llm.py — thin HTTP client for the local Ollama API.

Rule 1 compliance: OLLAMA_BASE_URL defaults to http://127.0.0.1:11434.
                   The code raises an error if the configured URL is not
                   a loopback address (127.x.x.x or ::1).
Rule 5 compliance: all prompt construction wraps document text in
                   <document_text> … </document_text> delimiters and
                   explicitly instructs the model to treat it as data.
"""
from __future__ import annotations

import json
import ipaddress
import socket
from typing import Any
from urllib.parse import urlparse

import requests

try:
    from src.config import LLM_TEMPERATURE, LLM_TIMEOUT_SECONDS, OLLAMA_BASE_URL, OLLAMA_MODEL
except ImportError:  # pragma: no cover
    from config import LLM_TEMPERATURE, LLM_TIMEOUT_SECONDS, OLLAMA_BASE_URL, OLLAMA_MODEL


# ---------------------------------------------------------------------------
# Safety guard — ensure we only talk to loopback
# ---------------------------------------------------------------------------

def _assert_loopback(url: str) -> None:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "http" or not host:
        raise RuntimeError("Ollama must use an HTTP URL on a loopback host.")
    if host == "localhost":
        return
    try:
        is_loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        try:
            addresses = socket.getaddrinfo(host, parsed.port or 80, type=socket.SOCK_STREAM)
        except socket.gaierror:
            addresses = []
        is_loopback = bool(addresses) and all(
            ipaddress.ip_address(address[4][0]).is_loopback for address in addresses
        )
    if not is_loopback:
        raise RuntimeError(
            f"Rule 1 violation: Ollama host '{host}' is not a loopback address. "
            "Data must not leave the device."
        )


_assert_loopback(OLLAMA_BASE_URL)


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class OllamaClient:
    """Minimal client for Ollama's /api/generate endpoint."""

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_MODEL,
        temperature: float = LLM_TEMPERATURE,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        _assert_loopback(self.base_url)
        self.model = model
        self.temperature = temperature

    # ------------------------------------------------------------------
    def generate(self, prompt: str, expect_json: bool = False) -> str:
        """
        Send a prompt and return the model's text response.

        Parameters
        ----------
        prompt      : fully-formed prompt string
        expect_json : if True, sets format='json' in the Ollama request
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": 2048,
            },
        }
        if expect_json:
            payload["format"] = "json"

        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=LLM_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()
        except requests.exceptions.ConnectionError as exc:
            raise RuntimeError(
                "Cannot reach the local Ollama service. Start Ollama and verify "
                "that the selected model is available with `ollama list`."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise RuntimeError(
                f"Local Ollama timed out after {LLM_TIMEOUT_SECONDS}s. "
                "Try again or increase LLM_TIMEOUT_SECONDS."
            ) from exc
        except requests.exceptions.HTTPError as exc:
            raise RuntimeError(
                f"Local Ollama returned HTTP {resp.status_code}; verify the model "
                "tag and local Ollama service."
            ) from exc

        try:
            data = resp.json()
        except ValueError as exc:
            raise RuntimeError("Local Ollama returned an invalid response.") from exc
        response = data.get("response")
        if not isinstance(response, str) or not response.strip():
            raise RuntimeError("Local Ollama returned an empty response.")
        return response.strip()

    def generate_json(self, prompt: str) -> dict | list:
        """Generate and parse JSON output. Raises ValueError on bad JSON."""
        raw = self.generate(prompt, expect_json=True)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            # Try to extract JSON from the response if it's wrapped in text
            import re
            match = re.search(r"\{.*\}|\[.*\]", raw, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise ValueError(
                f"Model returned non-JSON output:\n{raw[:300]}"
            ) from exc


# ---------------------------------------------------------------------------
# Prompt helpers — Rule 5 enforcement
# ---------------------------------------------------------------------------

def wrap_document_text(text: str) -> str:
    """
    Wrap untrusted document text in XML-like delimiters and add an
    instruction to ignore any embedded instructions (Rule 5).
    """
    try:
        from src.guard import safe_document_block
    except ImportError:  # pragma: no cover
        from guard import safe_document_block
    return safe_document_block(text)


# Module-level default client instance
default_client = OllamaClient()
