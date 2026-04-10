from types import SimpleNamespace

from config import Settings

from agents.con_agent import ConAgent, _coerce_research_payload, _coerce_search_plan_response


def test_coerce_research_payload_accepts_json_text():
    payload = _coerce_research_payload(
        '{"summary":"Search found real counter-evidence.","fact_points":["Point one.","Point two."]}'
    )

    assert payload.summary == "Search found real counter-evidence."
    assert payload.fact_points == ["Point one.", "Point two."]


def test_coerce_research_payload_falls_back_for_non_json_grounded_text():
    payload = _coerce_research_payload(
        "Search suggests the case is weaker than it looks.\n"
        "- Flattening management often reduces coaching depth.\n"
        "- AI automation gains depend on clean process design.\n"
    )

    assert "case is weaker" in payload.summary
    assert payload.fact_points


def test_coerce_research_payload_handles_missing_text():
    payload = _coerce_research_payload(None)

    assert payload.summary == "No grounded research summary returned."
    assert payload.fact_points == ["No grounded research summary returned."]


def test_coerce_search_plan_response_returns_default_for_truncated_json():
    response = SimpleNamespace(
        parsed=None,
        text='{"needs_search": true, "query": "latest Amazon layoff evidence',
    )

    payload = _coerce_search_plan_response(response)

    assert payload.needs_search is False
    assert payload.query is None


def test_run_grounded_research_handles_missing_text_and_candidates(monkeypatch):
    agent = ConAgent(
        Settings(
            groq_api_key="groq-test",
            gemini_api_key="gemini-test",
            tavily_api_key="tavily-test",
            mongodb_uri=None,
            mongodb_db_name="debate_arena_test",
            mongodb_strict_startup=True,
            mongodb_timeout_ms=8000,
            cors_origins=["http://localhost:5173"],
            host_model="llama-3.3-70b-versatile",
            pro_model="llama-3.3-70b-versatile",
            crowd_model="llama-3.3-70b-versatile",
            con_model="gemini-2.5-flash",
            judge_model="gemini-2.5-flash",
        )
    )

    async def _generate_content(*args, **kwargs):
        return SimpleNamespace(text=None, candidates=None)

    fake_client = SimpleNamespace(
        aio=SimpleNamespace(
            models=SimpleNamespace(generate_content=_generate_content)
        )
    )
    monkeypatch.setattr(agent, "_client_or_raise", lambda: fake_client)

    update = __import__("asyncio").run(agent.run_grounded_research("nuclear risks"))

    assert update.summary == "No grounded research summary returned."
    assert update.fact_context == "No grounded research summary returned."
    assert update.sources == []
