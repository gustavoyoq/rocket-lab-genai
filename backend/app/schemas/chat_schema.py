from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ChatAskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    session_id: str | None = None
    verbose: bool = True


class ChatAskResponse(BaseModel):
    session_id: str
    tool_call: str | None = None
    tool_result: str | None = None
    conclusion: str
    sql_executed: str
    confidence: str
    timestamp: datetime
    raw_response: str


class SessionResetResponse(BaseModel):
    session_id: str
    message: str


class ApiErrorResponse(BaseModel):
    code: str
    message: str
