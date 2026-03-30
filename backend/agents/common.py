from __future__ import annotations

import json
from typing import Iterable

from models import SearchSource


EXCLUDED_CONTEXT_TYPES = {
    "search_started",
    "search_complete",
    "search_error",
    "thinking",
    "system",
}


def _clean_point(message: str, limit: int = 140) -> str:
    point = " ".join(message.split())
    if len(point) <= limit:
        return point
    return f"{point[: limit - 3].rstrip()}..."


def truncate_words(text: str, limit: int) -> str:
    words = text.split()
    if len(words) <= limit:
        return " ".join(words)
    return f"{' '.join(words[:limit]).rstrip()}..."


def build_recent_context(history: list[dict], limit: int) -> str:
    relevant = [
        item
        for item in history
        if item.get("type") not in EXCLUDED_CONTEXT_TYPES
    ][-limit:]
    return "\n\n".join(
        f"[{item['agent'].upper()}] {item['message']}"
        for item in relevant
    )


def _agent_points(history: Iterable[dict], agent: str, limit: int = 3) -> list[str]:
    points = [
        _clean_point(item["message"])
        for item in history
        if item.get("agent") == agent and item.get("type") in {"argument", "judge_interrupt", "human"}
    ]
    return points[-limit:]


def summarize_debate_history(history: list[dict]) -> str:
    pro_points = _agent_points(history, "pro")
    con_points = _agent_points(history, "con")
    human_points = _agent_points(history, "human", limit=2)

    clashes = []
    if pro_points and con_points:
        clashes.append(
            "latest central clash "
            f"(Pro: {pro_points[-1]} / Con: {con_points[-1]})"
        )
    if human_points:
        clashes.append(f"audience pressure ({'; '.join(human_points)})")

    parts = [
        f"Pro argued: {'; '.join(pro_points) if pro_points else 'No major pro points recorded.'}",
        f"Con argued: {'; '.join(con_points) if con_points else 'No major con points recorded.'}",
        f"Human interventions: {'; '.join(human_points) if human_points else 'None.'}",
        f"Key clashes: {'; '.join(clashes) if clashes else 'No decisive clash yet.'}",
    ]
    return "\n".join(parts)


def parse_json_blob(text: str) -> dict:
    text = text.strip()
    if not text:
        return {}
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return {}
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}


def format_sources_for_prompt(sources: list[SearchSource], limit: int = 5) -> str:
    lines = []
    for source in sources[:limit]:
        lines.append(f"- {source.title}: {source.snippet} ({source.url})")
    return "\n".join(lines) if lines else "No external sources collected yet."
