from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import load_api_settings
from .routers.chat_router import router as chat_router
from .services.chat_service import ChatService
from .services.session_store import InMemorySessionStore
from src.text2sql.service import TextToSQLService

settings = load_api_settings()
app = FastAPI(
    title="Text2SQL RocketLab API",
    version="0.1.0",
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    core_service = TextToSQLService()
    app.state.chat_service = ChatService(
        core_service=core_service,
        session_store=InMemorySessionStore(),
    )


@app.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(chat_router)
