import asyncio
from datetime import UTC, datetime

from debate_manager import drain_interrupts, should_consider_crowd, should_request_verdict


def test_drain_interrupts_returns_messages_in_order():
    queue: asyncio.Queue[str] = asyncio.Queue()
    queue.put_nowait("First")
    queue.put_nowait("Second")

    drained = drain_interrupts(queue)

    assert drained == ["First", "Second"]
    assert queue.empty()


def test_should_request_verdict_waits_for_minimum_then_forces_on_cap():
    assert should_request_verdict(exchange_count=2, min_exchanges=4, max_exchanges=6, judge_signaled_end=True) is False
    assert should_request_verdict(exchange_count=4, min_exchanges=4, max_exchanges=6, judge_signaled_end=False) is False
    assert should_request_verdict(exchange_count=4, min_exchanges=4, max_exchanges=6, judge_signaled_end=True) is True
    assert should_request_verdict(exchange_count=6, min_exchanges=4, max_exchanges=6, judge_signaled_end=False) is True


def test_should_consider_crowd_throttles_back_to_back_reactions():
    history = [
        {
            "id": "pro-1",
            "agent": "pro",
            "type": "argument",
            "message": "Point made.",
            "metadata": {},
            "created_at": datetime(2026, 3, 30, 12, 0, tzinfo=UTC),
        },
        {
            "id": "crowd-1",
            "agent": "crowd",
            "type": "crowd_reaction",
            "message": "That landed.",
            "metadata": {},
            "created_at": datetime(2026, 3, 30, 12, 1, tzinfo=UTC),
        },
        {
            "id": "con-1",
            "agent": "con",
            "type": "argument",
            "message": "Counterpoint.",
            "metadata": {},
            "created_at": datetime(2026, 3, 30, 12, 2, tzinfo=UTC),
        },
    ]

    assert should_consider_crowd(history) is False

    history.append(
        {
            "id": "pro-2",
            "agent": "pro",
            "type": "argument",
            "message": "New point.",
            "metadata": {},
            "created_at": datetime(2026, 3, 30, 12, 3, tzinfo=UTC),
        }
    )

    assert should_consider_crowd(history) is True
