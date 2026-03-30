from __future__ import annotations

from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel

from agents.common import build_recent_context, parse_json_blob, summarize_debate_history
from config import Settings
from models import JudgeDecision


class _JudgeDecisionResponse(BaseModel):
    should_interrupt: bool = False
    interrupt_message: str | None = None
    should_end: bool = False
    reason: str | None = None


def _coerce_decision_payload(response: Any) -> _JudgeDecisionResponse:
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, _JudgeDecisionResponse):
        return parsed
    if isinstance(parsed, dict):
        return _JudgeDecisionResponse.model_validate(parsed)

    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        data = parse_json_blob(text)
        if data:
            return _JudgeDecisionResponse.model_validate(data)
        try:
            return _JudgeDecisionResponse.model_validate_json(text)
        except Exception:
            return _JudgeDecisionResponse()

    return _JudgeDecisionResponse()


def _response_text(response: Any, fallback: str) -> str:
    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()
    return fallback


EVALUATION_PROMPT = """You are PRADHAKSHINI in live arbitration mode.
Your job is not to grandstand. Your job is to keep the debate honest and decide when it has earned a verdict.

Return JSON only with:
- should_interrupt: boolean
- interrupt_message: string or null
- should_end: boolean
- reason: string or null

Rules:
- Interrupt only for a clearly wrong or seriously misleading factual claim
- Keep any interrupt message short and authoritative, 30 to 40 words max
- End the debate only if both sides have developed enough substance
- If the debate is still thin or repetitive, do not end it"""

VERDICT_PROMPT = """You are PRADHAKSHINI delivering the final verdict in THE ARENA.

Rules:
- 150 to 200 words
- Include a line exactly in the form: Winner: PRO or Winner: CON
- Include a line exactly in the form: Score: Pro X/10 | Con Y/10
- Name the strongest point from each side
- Explain the decisive edge
- Declare one clear winner
- End with one hard closing sentence
- Serious, decisive, elegant"""


class JudgeAgent:
    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.gemini_api_key
        self._model = settings.judge_model
        self._client: genai.Client | None = None

    def _client_or_raise(self) -> genai.Client:
        if not self._api_key:
            raise RuntimeError("Missing GEMINI_API_KEY for judge agent")
        if self._client is None:
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def _thinking_config(self):
        if "flash" in self._model:
            return types.ThinkingConfig(thinking_budget=0)
        return None

    async def evaluate_turn(
        self,
        topic: str,
        history: list[dict],
        exchange_count: int,
        interrupts_used: int,
        min_exchanges: int,
    ) -> JudgeDecision:
        recent_context = build_recent_context(history, 4) or "No recent exchange."
        response = await self._client_or_raise().aio.models.generate_content(
            model=self._model,
            contents=(
                f"Topic: {topic}\n\n"
                f"Recent exchange:\n{recent_context}\n\n"
                f"Completed exchanges: {exchange_count}\n"
                f"Interruptions already used: {interrupts_used}\n"
                f"Minimum exchanges before a verdict: {min_exchanges}"
            ),
            config=types.GenerateContentConfig(
                system_instruction=EVALUATION_PROMPT,
                response_mime_type="application/json",
                response_json_schema=_JudgeDecisionResponse.model_json_schema(),
                temperature=0.2,
                max_output_tokens=180,
                thinking_config=self._thinking_config(),
            ),
        )
        parsed = _coerce_decision_payload(response)
        return JudgeDecision(
            should_interrupt=parsed.should_interrupt,
            interrupt_message=parsed.interrupt_message,
            should_end=parsed.should_end,
            reason=parsed.reason,
        )

    async def final_verdict(self, topic: str, history: list[dict]) -> str:
        summary = summarize_debate_history(history)
        recent_context = build_recent_context(history, 4) or "No recent exchange."
        response = await self._client_or_raise().aio.models.generate_content(
            model=self._model,
            contents=(
                f"Topic: {topic}\n\n"
                f"Debate summary:\n{summary}\n\n"
                f"Final recent exchange:\n{recent_context}"
            ),
            config=types.GenerateContentConfig(
                system_instruction=VERDICT_PROMPT,
                temperature=0.45,
                max_output_tokens=260,
                thinking_config=self._thinking_config(),
            ),
        )
        return _response_text(
            response,
            "Winner: CON\nScore: Pro 5/10 | Con 6/10\nCon edged the debate by staying tighter on the factual burden and exposing the weaker assumption underneath the motion. The Arena rewards the side that made the cleaner case under pressure.",
        )
