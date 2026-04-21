from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    google_api_key: str
    model_name: str
    db_path: Path
    query_row_limit: int
    query_timeout_seconds: int
    max_history_messages: int


def load_settings() -> Settings:
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    model_name = os.getenv("MODEL_NAME", "gemini-2.5-flash-lite").strip()
    db_path = Path(os.getenv("DB_PATH", "./banco.db")).resolve()

    return Settings(
        google_api_key=api_key,
        model_name=model_name,
        db_path=db_path,
        query_row_limit=max(1, int(os.getenv("QUERY_ROW_LIMIT", "100"))),
        query_timeout_seconds=max(1, int(os.getenv("QUERY_TIMEOUT_SECONDS", "8"))),
        max_history_messages=max(2, int(os.getenv("MAX_HISTORY_MESSAGES", "20"))),
    )
