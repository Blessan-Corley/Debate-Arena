from datetime import UTC, datetime

import pytest

from storage import InMemoryDebateStore, _normalize_debate_document


@pytest.mark.asyncio
async def test_in_memory_store_tracks_messages_feedback_and_recent_history():
    store = InMemoryDebateStore()
    debate_id = await store.create_debate(
        topic="AI should replace managers",
        min_exchanges=4,
        models={"pro": "llama-3.3-70b-versatile", "con": "gemini-2.5-flash"},
    )

    await store.append_message(
        debate_id,
        {
            "id": "msg-1",
            "agent": "host",
            "type": "host_intro",
            "message": "Tonight, the floor is on fire.",
            "created_at": datetime.now(UTC),
            "metadata": {},
        },
    )
    await store.append_message(
        debate_id,
        {
            "id": "msg-2",
            "agent": "judge",
            "type": "judge_verdict",
            "message": "Con wins on substance.",
            "created_at": datetime.now(UTC),
            "metadata": {"winner": "con"},
        },
    )
    await store.finalize_debate(
        debate_id,
        winner="con",
        status="completed",
    )
    await store.save_feedback(
        debate_id,
        rating=5,
        comment="Good pacing.",
        winner_pick="con",
    )

    recent = await store.list_debates(limit=5)
    detail = await store.get_debate(debate_id)

    assert recent[0]["debate_id"] == debate_id
    assert recent[0]["message_count"] == 2
    assert recent[0]["winner"] == "con"
    assert detail["feedback"]["rating"] == 5
    assert detail["messages"][-1]["type"] == "judge_verdict"
    assert detail["messages"][-1]["metadata"]["winner"] == "con"


@pytest.mark.asyncio
async def test_in_memory_store_can_delete_debate_history():
    store = InMemoryDebateStore()
    debate_id = await store.create_debate(
        topic="Delete me",
        min_exchanges=4,
        models={"pro": "llama-3.3-70b-versatile"},
    )

    deleted = await store.delete_debate(debate_id)

    assert deleted is True
    assert await store.get_debate(debate_id) is None


def test_legacy_debate_documents_are_normalized_for_modern_history_reads():
    legacy_document = {
        "debate_id": "legacy-123",
        "topic": "Legacy archive debate",
        "messages": [
            {
                "agent": "host",
                "type": "host_intro",
                "content": "Welcome to the old arena.",
                "timestamp": "2026-03-25T10:00:00+00:00",
            },
            {
                "agent": "judge",
                "type": "judge_verdict",
                "message": "Con wins on consistency.",
                "metadata": {"winner": "con"},
                "created_at": "2026-03-25T10:05:00+00:00",
            },
        ],
    }

    normalized = _normalize_debate_document(legacy_document)

    assert normalized["debate_id"] == "legacy-123"
    assert normalized["status"] == "completed"
    assert normalized["winner"] == "con"
    assert normalized["message_count"] == 2
    assert normalized["min_exchanges"] == 4
    assert normalized["models"] == {}
    assert normalized["messages"][0]["message"] == "Welcome to the old arena."
    assert normalized["messages"][0]["id"].startswith("msg-")
    assert normalized["messages"][0]["created_at"].isoformat().startswith("2026-03-25T10:00:00")
