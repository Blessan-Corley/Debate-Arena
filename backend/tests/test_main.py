import asyncio

import pytest
from fastapi.testclient import TestClient

import main as main_module
from config import Settings
from main import create_app
from models import DebateEvent
from storage import InMemoryDebateStore


def _settings(
    *,
    mongodb_uri: str | None = None,
    mongodb_strict_startup: bool = False,
) -> Settings:
    return Settings(
        groq_api_key="groq-test",
        gemini_api_key="gemini-test",
        tavily_api_key="tavily-test",
        mongodb_uri=mongodb_uri,
        mongodb_db_name="debate_arena_test",
        mongodb_strict_startup=mongodb_strict_startup,
        mongodb_timeout_ms=8000,
        cors_origins=["http://localhost:5173"],
        host_model="llama-3.3-70b-versatile",
        pro_model="llama-3.3-70b-versatile",
        crowd_model="llama-3.3-70b-versatile",
        con_model="gemini-2.5-flash",
        judge_model="gemini-2.5-flash",
    )


def test_history_endpoint_returns_recent_debates():
    store = InMemoryDebateStore()
    debate_id = asyncio.run(
        store.create_debate(
            topic="AI should replace managers",
            min_exchanges=4,
            models={"pro": "llama-3.3-70b-versatile"},
        )
    )
    asyncio.run(store.finalize_debate(debate_id, winner="con", status="completed"))

    client = TestClient(create_app(settings=_settings(), store=store))
    response = client.get("/debate/history")

    assert response.status_code == 200
    assert response.json()[0]["debate_id"] == debate_id
    assert response.json()[0]["winner"] == "con"


def test_feedback_endpoint_rejects_invalid_rating():
    client = TestClient(create_app(settings=_settings(), store=InMemoryDebateStore()))

    response = client.post(
        "/debate/feedback",
        json={
            "debate_id": "debate-123",
            "rating": 7,
        },
    )

    assert response.status_code == 422


def test_delete_history_endpoint_removes_stored_debate():
    store = InMemoryDebateStore()
    debate_id = asyncio.run(
        store.create_debate(
            topic="Archive deletion",
            min_exchanges=4,
            models={"pro": "llama-3.3-70b-versatile"},
        )
    )

    client = TestClient(create_app(settings=_settings(), store=store))
    response = client.delete(f"/debate/history/{debate_id}")

    assert response.status_code == 200
    assert response.json() == {"status": "deleted"}
    assert asyncio.run(store.get_debate(debate_id)) is None


def test_delete_history_endpoint_returns_not_found_for_missing_debate():
    client = TestClient(create_app(settings=_settings(), store=InMemoryDebateStore()))

    response = client.delete("/debate/history/missing-debate")

    assert response.status_code == 404


class BrokenMongoStore:
    def __init__(self) -> None:
        self.closed = False
        self.ensure_indexes_calls = 0

    async def ensure_indexes(self) -> None:
        self.ensure_indexes_calls += 1
        raise RuntimeError("TLS handshake failed")

    async def close(self) -> None:
        self.closed = True

    async def list_debates(self, limit: int = 10):
        return []

    async def get_debate(self, debate_id: str):
        return None

    async def delete_debate(self, debate_id: str) -> bool:
        return False


def test_health_falls_back_to_memory_when_mongo_startup_fails():
    store = BrokenMongoStore()

    with TestClient(
        create_app(
            settings=_settings(mongodb_uri="mongodb://example.test"),
            store=store,
        )
    ) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["persistence"] == "memory"
    assert response.json()["startup_warning"] == "MongoDB unavailable. Running with in-memory history."
    assert store.ensure_indexes_calls == 1
    assert store.closed is True


def test_startup_raises_when_mongo_strict_mode_is_enabled():
    store = BrokenMongoStore()

    with pytest.raises(RuntimeError, match="TLS handshake failed"):
        with TestClient(
            create_app(
                settings=_settings(
                    mongodb_uri="mongodb://example.test",
                    mongodb_strict_startup=True,
                ),
                store=store,
            )
        ):
            pass


def test_start_debate_continues_when_mongo_fell_back_to_memory(monkeypatch):
    store = BrokenMongoStore()

    async def fake_run_debate(*, topic, min_exchanges, store, settings):
        yield DebateEvent(
            debate_id="debate-fallback",
            agent="system",
            type="debate_start",
            message=f"Starting {topic}",
            metadata={"min_exchanges": min_exchanges},
        )

    monkeypatch.setattr(main_module, "run_debate", fake_run_debate)

    with TestClient(
        create_app(
            settings=_settings(mongodb_uri="mongodb://example.test"),
            store=store,
        )
    ) as client:
        response = client.post(
            "/debate/start",
            json={
                "topic": "Persistence should be durable",
                "rounds": 4,
            },
        )

    assert response.status_code == 200
