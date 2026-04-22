from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass
from typing import Any


@dataclass
class SessionData:
    history: list[Any]
    updated_at: float


class InMemorySessionStore:
    def __init__(self):
        self._sessions: dict[str, SessionData] = {}
        self._lock = asyncio.Lock()

    async def get_or_create_session_id(self, session_id: str | None = None) -> str:
        if session_id:
            return session_id
        return str(uuid.uuid4())

    async def load_history(self, session_id: str) -> list[Any]:
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return []
            return list(session.history)

    async def save_history(self, session_id: str, history: list[Any]) -> None:
        async with self._lock:
            self._sessions[session_id] = SessionData(history=list(history), updated_at=time.time())

    async def reset_session(self, session_id: str) -> bool:
        async with self._lock:
            return self._sessions.pop(session_id, None) is not None
