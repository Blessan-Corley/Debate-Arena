from __future__ import annotations

import copy
import uuid
from datetime import UTC, datetime
from typing import Any, Protocol

import certifi
from pymongo import AsyncMongoClient, DESCENDING
from pymongo.server_api import ServerApi


def utc_now() -> datetime:
    return datetime.now(UTC)


def _coerce_datetime(value: Any, fallback: datetime) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except ValueError:
            return fallback
    return fallback


def _normalize_message(message: dict[str, Any], fallback_time: datetime) -> dict[str, Any]:
    created_at = _coerce_datetime(
        message.get("created_at") or message.get("timestamp"),
        fallback_time,
    )
    return {
        "id": message.get("id") or f"msg-{uuid.uuid4().hex}",
        "agent": message.get("agent", "system"),
        "type": message.get("type", "statement"),
        "message": message.get("message") or message.get("content") or "",
        "metadata": copy.deepcopy(message.get("metadata") or {}),
        "created_at": created_at,
    }


def _infer_winner(messages: list[dict[str, Any]]) -> str | None:
    for message in reversed(messages):
        winner = message.get("metadata", {}).get("winner")
        if winner:
            return winner
    return None


def _normalize_debate_document(document: dict[str, Any]) -> dict[str, Any]:
    now = utc_now()
    raw_messages = document.get("messages") or []
    normalized_messages = [
        _normalize_message(message, now)
        for message in raw_messages
        if isinstance(message, dict)
    ]

    created_candidates = [
        _coerce_datetime(document.get("created_at"), now),
        *(message["created_at"] for message in normalized_messages),
    ]
    created_at = min(created_candidates) if created_candidates else now

    updated_candidates = [
        _coerce_datetime(document.get("updated_at"), created_at),
        _coerce_datetime(document.get("ended_at"), created_at),
        *(message["created_at"] for message in normalized_messages),
    ]
    updated_at = max(updated_candidates) if updated_candidates else created_at
    ended_at = _coerce_datetime(document.get("ended_at"), updated_at) if document.get("ended_at") else None

    winner = document.get("winner") or _infer_winner(normalized_messages)
    status = document.get("status")
    if not status:
        status = "completed" if winner else ("running" if normalized_messages else "queued")

    feedback = copy.deepcopy(document.get("feedback")) if document.get("feedback") else None
    if isinstance(feedback, dict) and feedback.get("submitted_at"):
        feedback["submitted_at"] = _coerce_datetime(feedback["submitted_at"], updated_at)

    normalized = {
        "debate_id": str(document.get("debate_id") or document.get("id") or uuid.uuid4()),
        "topic": document.get("topic") or document.get("title") or "Untitled debate",
        "status": status,
        "winner": winner,
        "min_exchanges": int(document.get("min_exchanges") or 4),
        "models": copy.deepcopy(document.get("models") or {}),
        "messages": normalized_messages,
        "message_count": int(document.get("message_count") or len(normalized_messages)),
        "feedback": feedback,
        "created_at": created_at,
        "updated_at": updated_at,
        "ended_at": ended_at,
    }
    return normalized


def _debate_document(topic: str, min_exchanges: int, models: dict[str, str]) -> dict[str, Any]:
    now = utc_now()
    return {
        "debate_id": str(uuid.uuid4()),
        "schema_version": 2,
        "topic": topic,
        "status": "queued",
        "winner": None,
        "min_exchanges": min_exchanges,
        "models": models,
        "messages": [],
        "message_count": 0,
        "feedback": None,
        "created_at": now,
        "updated_at": now,
        "ended_at": None,
    }


def _debate_summary(document: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_debate_document(document)
    return {
        "debate_id": normalized["debate_id"],
        "topic": normalized["topic"],
        "status": normalized["status"],
        "winner": normalized.get("winner"),
        "message_count": normalized["message_count"],
        "created_at": normalized["created_at"],
        "updated_at": normalized["updated_at"],
        "ended_at": normalized.get("ended_at"),
        "feedback": normalized.get("feedback"),
    }


class DebateStore(Protocol):
    async def create_debate(
        self,
        topic: str,
        min_exchanges: int,
        models: dict[str, str],
    ) -> str: ...

    async def append_message(self, debate_id: str, message: dict[str, Any]) -> None: ...

    async def finalize_debate(self, debate_id: str, winner: str | None, status: str) -> None: ...

    async def save_feedback(
        self,
        debate_id: str,
        rating: int,
        comment: str | None,
        winner_pick: str | None,
    ) -> None: ...

    async def list_debates(self, limit: int = 10) -> list[dict[str, Any]]: ...

    async def get_debate(self, debate_id: str) -> dict[str, Any] | None: ...

    async def delete_debate(self, debate_id: str) -> bool: ...


class InMemoryDebateStore:
    def __init__(self) -> None:
        self._debates: dict[str, dict[str, Any]] = {}

    async def create_debate(
        self,
        topic: str,
        min_exchanges: int,
        models: dict[str, str],
    ) -> str:
        document = _debate_document(topic, min_exchanges, models)
        self._debates[document["debate_id"]] = document
        return document["debate_id"]

    async def append_message(self, debate_id: str, message: dict[str, Any]) -> None:
        document = self._debates[debate_id]
        document["messages"].append(copy.deepcopy(message))
        document["message_count"] += 1
        document["status"] = "running"
        document["updated_at"] = utc_now()

    async def finalize_debate(self, debate_id: str, winner: str | None, status: str) -> None:
        document = self._debates[debate_id]
        document["winner"] = winner
        document["status"] = status
        document["ended_at"] = utc_now()
        document["updated_at"] = document["ended_at"]

    async def save_feedback(
        self,
        debate_id: str,
        rating: int,
        comment: str | None,
        winner_pick: str | None,
    ) -> None:
        document = self._debates[debate_id]
        document["feedback"] = {
            "rating": rating,
            "comment": comment,
            "winner_pick": winner_pick,
            "submitted_at": utc_now(),
        }
        document["updated_at"] = utc_now()

    async def list_debates(self, limit: int = 10) -> list[dict[str, Any]]:
        debates = sorted(
            self._debates.values(),
            key=lambda item: item["updated_at"],
            reverse=True,
        )
        return [_debate_summary(copy.deepcopy(item)) for item in debates[:limit]]

    async def get_debate(self, debate_id: str) -> dict[str, Any] | None:
        document = self._debates.get(debate_id)
        return copy.deepcopy(document) if document else None

    async def delete_debate(self, debate_id: str) -> bool:
        if debate_id not in self._debates:
            return False
        del self._debates[debate_id]
        return True


class MongoDebateStore:
    def __init__(self, uri: str, db_name: str, timeout_ms: int = 8000) -> None:
        self._client = AsyncMongoClient(
            uri,
            appname="debate-arena",
            server_api=ServerApi("1"),
            tls=True,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=timeout_ms,
            connectTimeoutMS=timeout_ms,
            socketTimeoutMS=timeout_ms,
        )
        self._collection = self._client[db_name]["debates"]

    async def ensure_indexes(self) -> None:
        await self.ping()
        await self._collection.create_index("debate_id", unique=True)
        await self._collection.create_index([("updated_at", DESCENDING)])
        await self._migrate_legacy_documents()

    async def ping(self) -> None:
        await self._client.admin.command("ping")

    async def _migrate_legacy_documents(self) -> None:
        now = utc_now()
        await self._collection.update_many(
            {"schema_version": {"$exists": False}},
            {
                "$set": {
                    "schema_version": 2,
                    "models": {},
                    "min_exchanges": 4,
                },
                "$setOnInsert": {"created_at": now},
            },
        )
        await self._collection.update_many(
            {"message_count": {"$exists": False}},
            [{"$set": {"message_count": {"$size": {"$ifNull": ["$messages", []]}}}}],
        )

    async def close(self) -> None:
        await self._client.close()

    async def create_debate(
        self,
        topic: str,
        min_exchanges: int,
        models: dict[str, str],
    ) -> str:
        document = _debate_document(topic, min_exchanges, models)
        await self._collection.insert_one(document)
        return document["debate_id"]

    async def append_message(self, debate_id: str, message: dict[str, Any]) -> None:
        await self._collection.update_one(
            {"debate_id": debate_id},
            {
                "$push": {"messages": copy.deepcopy(message)},
                "$set": {"status": "running", "updated_at": utc_now()},
                "$inc": {"message_count": 1},
            },
        )

    async def finalize_debate(self, debate_id: str, winner: str | None, status: str) -> None:
        finished_at = utc_now()
        await self._collection.update_one(
            {"debate_id": debate_id},
            {
                "$set": {
                    "winner": winner,
                    "status": status,
                    "ended_at": finished_at,
                    "updated_at": finished_at,
                }
            },
        )

    async def save_feedback(
        self,
        debate_id: str,
        rating: int,
        comment: str | None,
        winner_pick: str | None,
    ) -> None:
        await self._collection.update_one(
            {"debate_id": debate_id},
            {
                "$set": {
                    "feedback": {
                        "rating": rating,
                        "comment": comment,
                        "winner_pick": winner_pick,
                        "submitted_at": utc_now(),
                    },
                    "updated_at": utc_now(),
                }
            },
        )

    async def list_debates(self, limit: int = 10) -> list[dict[str, Any]]:
        documents = [document async for document in self._collection.find({}, {"_id": 0})]
        normalized = [_normalize_debate_document(document) for document in documents]
        normalized.sort(key=lambda item: item["updated_at"], reverse=True)
        return [_debate_summary(document) for document in normalized[:limit]]

    async def get_debate(self, debate_id: str) -> dict[str, Any] | None:
        document = await self._collection.find_one({"debate_id": debate_id}, {"_id": 0})
        if not document:
            return None
        return _normalize_debate_document(document)

    async def delete_debate(self, debate_id: str) -> bool:
        result = await self._collection.delete_one({"debate_id": debate_id})
        return result.deleted_count > 0
