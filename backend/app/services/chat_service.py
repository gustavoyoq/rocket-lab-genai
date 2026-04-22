from __future__ import annotations

import re
from datetime import datetime, timezone

from src.text2sql.service import TextToSQLService

from ..schemas.chat_schema import ChatAskResponse
from .session_store import InMemorySessionStore


class ChatService:
    def __init__(self, core_service: TextToSQLService, session_store: InMemorySessionStore):
        self.core_service = core_service
        self.session_store = session_store

    def _extract_block(self, pattern: str, text: str) -> str | None:
        match = re.search(pattern, text, flags=re.DOTALL)
        if not match:
            return None
        return match.group(1).strip()

    def _parse_response(self, raw_response: str) -> dict[str, str | None]:
        tool_call = self._extract_block(r"\[TOOL CALL\]\s*(.*?)\n", raw_response)
        tool_result = self._extract_block(r"\[TOOL RESULT\]\s*(.*?)\n\nConclusao:", raw_response)
        conclusion = self._extract_block(r"Conclusao:\s*(.*?)\n\nSQL executado:", raw_response) or ""
        sql_executed = self._extract_block(r"SQL executado:\s*(.*?)\n\nConfianca:", raw_response) or ""
        confidence = self._extract_block(r"Confianca:\s*(.*)$", raw_response) or ""
        return {
            "tool_call": tool_call,
            "tool_result": tool_result,
            "conclusion": conclusion,
            "sql_executed": sql_executed,
            "confidence": confidence,
        }

    async def ask(self, question: str, session_id: str | None, verbose: bool) -> ChatAskResponse:
        final_session_id = await self.session_store.get_or_create_session_id(session_id)
        history = await self.session_store.load_history(final_session_id)

        raw_response, new_history = await self.core_service.ask(
            question=question,
            message_history=history,
            verbose=verbose,
        )
        await self.session_store.save_history(final_session_id, new_history)

        parsed = self._parse_response(raw_response)
        return ChatAskResponse(
            session_id=final_session_id,
            tool_call=parsed["tool_call"],
            tool_result=parsed["tool_result"],
            conclusion=parsed["conclusion"] or "",
            sql_executed=parsed["sql_executed"] or "",
            confidence=parsed["confidence"] or "",
            timestamp=datetime.now(timezone.utc),
            raw_response=raw_response,
        )
