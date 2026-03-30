from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class DebateStartRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=500)
    rounds: int = Field(default=4, ge=2, le=6)

    @field_validator("topic")
    @classmethod
    def normalize_topic(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 3:
            raise ValueError("Topic must be at least 3 non-space characters")
        return normalized


class InterruptRequest(BaseModel):
    debate_id: str = Field(min_length=3)
    message: str = Field(min_length=1, max_length=280)

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Interrupt message cannot be blank")
        return normalized


class FeedbackRequest(BaseModel):
    debate_id: str = Field(min_length=3)
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=500)
    winner_pick: Literal["pro", "con", "tie"] | None = None

    @field_validator("comment")
    @classmethod
    def normalize_comment(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class SearchSource(BaseModel):
    title: str
    url: str
    snippet: str
    provider: Literal["tavily", "google-search"]


class DebateMessage(BaseModel):
    id: str = Field(default_factory=lambda: f"msg-{uuid4().hex}")
    agent: str
    type: str
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class DebateEvent(BaseModel):
    id: str = Field(default_factory=lambda: f"evt-{uuid4().hex}")
    debate_id: str
    agent: str
    type: str
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)

    def to_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "debate_id": self.debate_id,
            "agent": self.agent,
            "type": self.type,
            "message": self.message,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


class DebateHistorySummary(BaseModel):
    debate_id: str
    topic: str
    status: str
    winner: str | None = None
    message_count: int
    created_at: datetime
    updated_at: datetime
    ended_at: datetime | None = None
    feedback: dict[str, Any] | None = None


class DebateHistoryDetail(DebateHistorySummary):
    models: dict[str, str]
    min_exchanges: int
    messages: list[DebateMessage]


class SearchPlan(BaseModel):
    needs_search: bool = False
    query: str | None = None
    reason: str | None = None


class ResearchUpdate(BaseModel):
    provider: Literal["tavily", "google-search"]
    summary: str
    fact_context: str
    sources: list[SearchSource] = Field(default_factory=list)
    query: str | None = None
    search_queries: list[str] = Field(default_factory=list)


class CrowdReaction(BaseModel):
    react: bool = False
    message: str | None = None


class JudgeDecision(BaseModel):
    should_interrupt: bool = False
    interrupt_message: str | None = None
    should_end: bool = False
    reason: str | None = None
