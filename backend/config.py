from __future__ import annotations

import os
from dataclasses import dataclass


def _split_csv(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    groq_api_key: str | None
    gemini_api_key: str | None
    tavily_api_key: str | None
    mongodb_uri: str | None
    mongodb_db_name: str
    mongodb_strict_startup: bool
    mongodb_timeout_ms: int
    cors_origins: list[str]
    host_model: str
    pro_model: str
    crowd_model: str
    con_model: str
    judge_model: str


def get_settings() -> Settings:
    return Settings(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
        mongodb_uri=os.getenv("MONGODB_URI"),
        mongodb_db_name=os.getenv("MONGODB_DB_NAME", "debate_arena"),
        mongodb_strict_startup=_parse_bool(os.getenv("MONGODB_STRICT_STARTUP"), True),
        mongodb_timeout_ms=int(os.getenv("MONGODB_TIMEOUT_MS", "8000")),
        cors_origins=_split_csv(
            os.getenv("CORS_ORIGINS"),
            ["http://localhost:5173", "http://localhost:3000"],
        ),
        host_model=os.getenv("GROQ_HOST_MODEL", "llama-3.3-70b-versatile"),
        pro_model=os.getenv("GROQ_PRO_MODEL", "llama-3.3-70b-versatile"),
        crowd_model=os.getenv("GROQ_CROWD_MODEL", "llama-3.3-70b-versatile"),
        con_model=os.getenv("GEMINI_CON_MODEL", "gemini-2.5-flash"),
        judge_model=os.getenv("GEMINI_JUDGE_MODEL", "gemini-2.5-flash"),
    )
