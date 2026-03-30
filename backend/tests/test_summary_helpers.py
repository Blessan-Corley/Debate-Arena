from datetime import UTC, datetime, timedelta

from agents.common import build_recent_context, summarize_debate_history


def _message(agent: str, kind: str, message: str, offset: int) -> dict:
    return {
        "id": f"{agent}-{offset}",
        "agent": agent,
        "type": kind,
        "message": message,
        "metadata": {},
        "created_at": datetime(2026, 3, 30, 12, 0, tzinfo=UTC) + timedelta(minutes=offset),
    }


def test_build_recent_context_limits_messages_in_order():
    history = [
        _message("host", "host_intro", "Opening", 0),
        _message("pro", "argument", "Point one for the motion.", 1),
        _message("con", "argument", "Counterpoint one against it.", 2),
        _message("human", "human", "What about workers?", 3),
        _message("pro", "argument", "Point two for the motion.", 4),
        _message("con", "argument", "Counterpoint two against it.", 5),
        _message("judge", "judge_interrupt", "That claim overstates the evidence.", 6),
    ]

    context = build_recent_context(history, limit=4)

    assert "[HUMAN] What about workers?" in context
    assert "[JUDGE] That claim overstates the evidence." in context
    assert "Opening" not in context


def test_summarize_debate_history_groups_key_points():
    history = [
        _message("pro", "argument", "AI managers remove repetitive oversight and improve consistency.", 1),
        _message("con", "argument", "They erase accountability and flatten local judgment.", 2),
        _message("human", "human", "Would that hurt trust?", 3),
        _message("pro", "argument", "Trust rises when performance decisions become less arbitrary.", 4),
        _message("con", "argument", "The problem is not arbitrariness alone; it is context blindness.", 5),
    ]

    summary = summarize_debate_history(history)

    assert "Pro argued" in summary
    assert "Con argued" in summary
    assert "Human interventions" in summary
    assert "Key clashes" in summary


def test_summarize_debate_history_prefers_latest_points_over_early_ones():
    history = [
        _message("pro", "argument", "Early pro point.", 1),
        _message("con", "argument", "Early con point.", 2),
        _message("pro", "argument", "Middle pro point.", 3),
        _message("con", "argument", "Middle con point.", 4),
        _message("pro", "argument", "Late pro point.", 5),
        _message("con", "argument", "Late con point.", 6),
    ]

    summary = summarize_debate_history(history)

    assert "Late pro point." in summary
    assert "Late con point." in summary
