from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from config import Settings, get_settings
from debate_manager import active_debates, run_debate
from models import (
    DebateHistoryDetail,
    DebateHistorySummary,
    DebateStartRequest,
    FeedbackRequest,
    InterruptRequest,
)
from storage import InMemoryDebateStore, MongoDebateStore


load_dotenv(Path(__file__).with_name(".env"))


logger = logging.getLogger(__name__)


def _build_store(settings: Settings):
    if settings.mongodb_uri:
        return MongoDebateStore(
            settings.mongodb_uri,
            settings.mongodb_db_name,
            timeout_ms=settings.mongodb_timeout_ms,
        )
    return InMemoryDebateStore()


def _require_llm_keys(settings: Settings) -> None:
    missing = [
        name
        for name, value in {
            "GROQ_API_KEY": settings.groq_api_key,
            "GEMINI_API_KEY": settings.gemini_api_key,
            "TAVILY_API_KEY": settings.tavily_api_key,
        }.items()
        if not value
    ]
    if missing:
        joined = ", ".join(missing)
        raise HTTPException(
            status_code=503,
            detail=f"Missing required AI configuration: {joined}",
        )


def create_app(settings: Settings | None = None, store: Any | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    resolved_store = store or _build_store(resolved_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.startup_warning = None
        active_store = app.state.store
        ensure_indexes = getattr(active_store, "ensure_indexes", None)
        if callable(ensure_indexes):
            try:
                await ensure_indexes()
            except Exception as exc:
                if resolved_settings.mongodb_uri and not resolved_settings.mongodb_strict_startup:
                    logger.warning(
                        "Mongo startup failed, falling back to in-memory store: %s",
                        exc,
                    )
                    failed_store = active_store
                    fallback_store = InMemoryDebateStore()
                    app.state.store = fallback_store
                    app.state.startup_warning = "MongoDB unavailable. Running with in-memory history."
                    close_failed = getattr(failed_store, "close", None)
                    if callable(close_failed):
                        await close_failed()
                else:
                    raise
        try:
            yield
        finally:
            close = getattr(app.state.store, "close", None)
            if callable(close):
                await close()

    app = FastAPI(title="Debate Arena API", lifespan=lifespan)
    app.state.settings = resolved_settings
    app.state.store = resolved_store

    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "active_debates": len(active_debates),
            "persistence": "mongo" if isinstance(app.state.store, MongoDebateStore) else "memory",
            "startup_warning": app.state.startup_warning,
        }

    @app.get("/debate/history", response_model=list[DebateHistorySummary])
    async def list_history(limit: int = Query(default=30, ge=1, le=100)):
        return await app.state.store.list_debates(limit=limit)

    @app.get("/debate/history/{debate_id}", response_model=DebateHistoryDetail)
    async def get_history(debate_id: str):
        debate = await app.state.store.get_debate(debate_id)
        if not debate:
            raise HTTPException(status_code=404, detail="Debate not found")
        return debate

    @app.delete("/debate/history/{debate_id}")
    async def delete_history(debate_id: str):
        if debate_id in active_debates:
            raise HTTPException(status_code=409, detail="Cannot delete a debate while it is still running")
        deleted = await app.state.store.delete_debate(debate_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Debate not found")
        return {"status": "deleted"}

    @app.post("/debate/start")
    async def start_debate(request: DebateStartRequest):
        topic = request.topic.strip()
        if len(topic) < 3:
            raise HTTPException(status_code=400, detail="Topic must be at least 3 characters")
        _require_llm_keys(app.state.settings)

        async def event_generator():
            async for event in run_debate(
                topic=topic,
                min_exchanges=request.rounds,
                store=app.state.store,
                settings=app.state.settings,
            ):
                yield {
                    "event": event.type,
                    "data": json.dumps(event.to_payload()),
                }

        return EventSourceResponse(event_generator(), ping=15)

    @app.post("/debate/interrupt")
    async def interrupt_debate(request: InterruptRequest):
        queue = active_debates.get(request.debate_id)
        if not queue:
            raise HTTPException(status_code=404, detail="Debate not found or already concluded")
        await queue.put(request.message.strip())
        return {"status": "queued"}

    @app.post("/debate/feedback")
    async def submit_feedback(request: FeedbackRequest):
        debate = await app.state.store.get_debate(request.debate_id)
        if not debate:
            raise HTTPException(status_code=404, detail="Debate not found")
        await app.state.store.save_feedback(
            request.debate_id,
            rating=request.rating,
            comment=request.comment,
            winner_pick=request.winner_pick,
        )
        return {"status": "received"}

    return app


app = create_app()
