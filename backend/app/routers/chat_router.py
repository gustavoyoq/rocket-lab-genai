from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ..schemas.chat_schema import ChatAskRequest, ChatAskResponse, SessionResetResponse
from ..services.chat_service import ChatService
from ..services.session_store import InMemorySessionStore
from src.text2sql.service import TextToSQLService

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


def _get_chat_service(request: Request) -> ChatService:
    if not hasattr(request.app.state, "chat_service"):
        request.app.state.chat_service = ChatService(
            core_service=TextToSQLService(),
            session_store=InMemorySessionStore(),
        )
    return request.app.state.chat_service


@router.post("/ask", response_model=ChatAskResponse)
async def ask_agent(payload: ChatAskRequest, request: Request) -> ChatAskResponse:
    chat_service = _get_chat_service(request)
    try:
        return await chat_service.ask(
            question=payload.question,
            session_id=payload.session_id,
            verbose=payload.verbose,
        )
    except Exception as exc:
        error_text = str(exc)
        if "status_code: 429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
            raise HTTPException(status_code=429, detail="Limite de cota da API temporariamente excedido.")
        if "API key" in error_text or "API_KEY_INVALID" in error_text:
            raise HTTPException(status_code=401, detail="Chave de API invalida ou expirada.")
        raise HTTPException(status_code=500, detail=error_text)


@router.delete("/sessions/{session_id}", response_model=SessionResetResponse)
async def reset_session(session_id: str, request: Request) -> SessionResetResponse:
    chat_service = _get_chat_service(request)
    removed = await chat_service.session_store.reset_session(session_id)
    message = "Sessao removida com sucesso." if removed else "Sessao nao existia, nada para remover."
    return SessionResetResponse(session_id=session_id, message=message)
