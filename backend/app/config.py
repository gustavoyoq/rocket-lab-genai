from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ApiSettings:
    host: str
    port: int
    debug: bool
    cors_origins: list[str]


def load_api_settings() -> ApiSettings:
    raw_origins = os.getenv("API_CORS_ORIGINS", "*").strip()
    origins = [item.strip() for item in raw_origins.split(",") if item.strip()]
    if not origins:
        origins = ["*"]

    return ApiSettings(
        host=os.getenv("API_HOST", "0.0.0.0").strip(),
        port=int(os.getenv("API_PORT", "8000")),
        debug=os.getenv("API_DEBUG", "true").lower() in {"1", "true", "yes"},
        cors_origins=origins,
    )
