from __future__ import annotations

from groq import AsyncGroq

from config import Settings


SYSTEM_PROMPT = """You are GOPINATH, the host of THE ARENA.
You speak once at the very start of the debate.

Style:
- Confident, cinematic, charismatic
- Short and sharp, never cheesy
- Set the stage and get out of the way

Rules:
- 40 to 60 words
- Introduce the topic, Blessan for Pro, and Pranav for Con
- Make it feel like a serious live debate show"""


class HostAgent:
    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.groq_api_key
        self._model = settings.host_model
        self._client: AsyncGroq | None = None

    def _client_or_raise(self) -> AsyncGroq:
        if not self._api_key:
            raise RuntimeError("Missing GROQ_API_KEY for host agent")
        if self._client is None:
            self._client = AsyncGroq(api_key=self._api_key)
        return self._client

    async def introduce(self, topic: str) -> str:
        response = await self._client_or_raise().chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Topic: {topic}\n"
                        "Open the debate with one dramatic, elegant introduction."
                    ),
                },
            ],
            temperature=0.8,
            max_tokens=96,
        )
        return response.choices[0].message.content.strip()
