from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from models import DebateEvent, DebateStartRequest, FeedbackRequest, InterruptRequest


def test_debate_event_serializes_with_message_and_metadata():
    event = DebateEvent(
        debate_id="debate-123",
        agent="pro",
        type="search_complete",
        message="Victor found three live sources.",
        metadata={"provider": "tavily", "source_count": 3},
        created_at=datetime(2026, 3, 30, 12, 0, tzinfo=UTC),
    )

    payload = event.to_payload()

    assert payload["id"].startswith("evt-")
    assert payload["message"] == "Victor found three live sources."
    assert payload["metadata"]["provider"] == "tavily"
    assert payload["created_at"].startswith("2026-03-30T12:00:00")


def test_feedback_rating_must_be_between_one_and_five():
    with pytest.raises(ValidationError):
        FeedbackRequest(
            debate_id="debate-123",
            rating=7,
            comment="Too long.",
        )


def test_topic_and_interrupt_reject_whitespace_only_input():
    with pytest.raises(ValidationError):
        DebateStartRequest(topic="   ", rounds=4)

    with pytest.raises(ValidationError):
        InterruptRequest(debate_id="debate-123", message="   ")
