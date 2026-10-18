from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from typing import Any

try:
    from src.config import SESSION_TTL_SECONDS
except ImportError:  # pragma: no cover
    from config import SESSION_TTL_SECONDS


@dataclass
class SessionRecord:
    session_id: str
    created_at: float
    expires_at: float
    document_name: str = ""
    summary: str = ""
    key_clauses: list[dict[str, Any]] = field(default_factory=list)
    source_clauses: list[dict[str, Any]] = field(default_factory=list)
    status: dict[str, Any] = field(default_factory=lambda: {"stage": "pending", "done": 0, "total": 0})
    data: dict[str, Any] = field(default_factory=dict)


class SessionStore:
    def __init__(self, ttl_seconds: int = SESSION_TTL_SECONDS) -> None:
        self.ttl_seconds = ttl_seconds
        self._sessions: dict[str, SessionRecord] = {}

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [sid for sid, record in self._sessions.items() if record.expires_at <= now]
        for sid in expired:
            del self._sessions[sid]

    def create(self, document_name: str = "") -> SessionRecord:
        self._purge_expired()
        sid = secrets.token_hex(8)
        now = time.time()
        record = SessionRecord(
            session_id=sid,
            created_at=now,
            expires_at=now + self.ttl_seconds,
            document_name=document_name,
        )
        self._sessions[sid] = record
        return record

    def get(self, session_id: str) -> SessionRecord | None:
        self._purge_expired()
        record = self._sessions.get(session_id)
        if record is None:
            return None
        if record.expires_at <= time.time():
            del self._sessions[session_id]
            return None
        return record

    def delete(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    def list(self) -> list[SessionRecord]:
        self._purge_expired()
        return list(self._sessions.values())


store = SessionStore()
