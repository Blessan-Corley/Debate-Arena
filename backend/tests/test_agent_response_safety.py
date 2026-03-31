from groq import RateLimitError

from config import Settings
from types import SimpleNamespace

from agents.pro import ProAgent
from agents.con_agent import _response_text as con_response_text
from agents.judge import _coerce_decision_payload, _response_text as judge_response_text
from agents.pro import _response_text as pro_response_text


def test_pro_response_text_falls_back_when_groq_content_missing():
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=None))]
    )

    assert pro_response_text(response, fallback="Fallback line.") == "Fallback line."


def test_con_response_text_falls_back_when_gemini_text_missing():
    response = SimpleNamespace(text=None)

    assert con_response_text(response, fallback="Fallback rebuttal.") == "Fallback rebuttal."


def test_judge_decision_payload_defaults_when_text_and_parsed_are_missing():
    response = SimpleNamespace(parsed=None, text=None)

    payload = _coerce_decision_payload(response)

    assert payload.should_interrupt is False
    assert payload.should_end is False


def test_judge_response_text_falls_back_when_verdict_text_missing():
    response = SimpleNamespace(text=None)

    assert judge_response_text(response, fallback="Winner: CON\nScore: Pro 4/10 | Con 7/10") == "Winner: CON\nScore: Pro 4/10 | Con 7/10"


def test_pro_follow_up_plan_returns_default_when_provider_call_fails(monkeypatch):
    agent = ProAgent(
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

    class _RaisingCompletions:
        async def create(self, *args, **kwargs):
            response = SimpleNamespace(request=None, status_code=429, headers={}, text="", json=lambda: {})
            raise RateLimitError("rate limited", response=response, body={})

    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=_RaisingCompletions()))
    monkeypatch.setattr(agent, "_llm_or_raise", lambda: fake_client)

    plan = __import__("asyncio").run(
        agent.plan_follow_up_search("Topic", [{"agent": "con", "type": "argument", "message": "Point"}], None)
    )

    assert plan.needs_search is False
    assert plan.query is None
