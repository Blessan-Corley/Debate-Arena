from __future__ import annotations

from groq import AsyncGroq

from agents.common import build_recent_context, parse_json_blob
from config import Settings
from models import CrowdReaction


SYSTEM_PROMPT = """You are THE CROWD on THE ARENA.
You only speak when a point genuinely lands.

Return JSON only with:
- react: boolean
- message: string or null

Rules:
- If the point was ordinary, set react to false
- Default to false unless the point clearly lands above average
- If you react, write 10 to 20 words
- Witty, earned, sharp
- No emoji, no meme slang, no monologues"""


class CrowdAgent:
    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.groq_api_key
        self._model = settings.crowd_model
        self._client: AsyncGroq | None = None

    def _client_or_raise(self) -> AsyncGroq:
        if not self._api_key:
            raise RuntimeError("Missing GROQ_API_KEY for crowd agent")
        if self._client is None:
            self._client = AsyncGroq(api_key=self._api_key)
        return self._client

    async def maybe_react(self, topic: str, history: list[dict]) -> CrowdReaction:
        recent = build_recent_context(history, 2) or "No recent exchange."
        response = await self._client_or_raise().chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Topic: {topic}\n\nRecent exchange:\n{recent}",
                },
            ],
            temperature=0.7,
            max_tokens=40,
        )
        data = parse_json_blob(response.choices[0].message.content or "")
        return CrowdReaction.model_validate(data or {})
