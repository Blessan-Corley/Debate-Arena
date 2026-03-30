from __future__ import annotations

from groq import AsyncGroq
from tavily import AsyncTavilyClient

from agents.common import build_recent_context, format_sources_for_prompt, parse_json_blob, truncate_words
from config import Settings
from models import ResearchUpdate, SearchPlan, SearchSource


PLAN_PROMPT = """You are the Pro debater's research planner.
Return JSON only with:
- needs_search: boolean
- query: string or null
- reason: string or null

Search only when the recent exchange needs a fresh factual check, a current example, or a precise counter.
Do not search for general philosophy or broad rhetoric."""

ARGUMENT_PROMPT = """You are BLESSAN, the Pro debater on THE ARENA.
You argue strongly for the motion.

Voice:
- Sharp, confident, intellectually aggressive
- Willing to disagree with the audience if they are wrong
- Never generic, never repetitive

Rules:
- 50 to 80 words
- One strong argument, not a list
- Directly answer the latest Con or Human pressure point
- If you use facts, make them sound current and specific
- End with a clean punch, not a speech"""


def _response_text(response, fallback: str) -> str:
    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, KeyError, TypeError):
        content = None

    if isinstance(content, str) and content.strip():
        return content.strip()
    return fallback


class ProAgent:
    def __init__(self, settings: Settings) -> None:
        self._groq_api_key = settings.groq_api_key
        self._tavily_api_key = settings.tavily_api_key
        self._model = settings.pro_model
        self._llm: AsyncGroq | None = None
        self._search: AsyncTavilyClient | None = None
        self._fact_notes: list[str] = []
        self._sources: list[SearchSource] = []
        self._follow_up_searches = 0

    def _llm_or_raise(self) -> AsyncGroq:
        if not self._groq_api_key:
            raise RuntimeError("Missing GROQ_API_KEY for pro agent")
        if self._llm is None:
            self._llm = AsyncGroq(api_key=self._groq_api_key)
        return self._llm

    def _search_or_raise(self) -> AsyncTavilyClient:
        if not self._tavily_api_key:
            raise RuntimeError("Missing TAVILY_API_KEY for pro agent")
        if self._search is None:
            self._search = AsyncTavilyClient(api_key=self._tavily_api_key)
        return self._search

    def apply_research(self, update: ResearchUpdate) -> None:
        self._fact_notes.append(update.fact_context)
        self._fact_notes = self._fact_notes[-6:]
        self._sources.extend(update.sources)
        self._sources = self._sources[-12:]

    async def initial_research(self, topic: str) -> ResearchUpdate:
        query = f"{topic} strongest evidence data studies arguments in favor"
        update = await self.run_search(query)
        self.apply_research(update)
        return update

    async def run_search(self, query: str) -> ResearchUpdate:
        response = await self._search_or_raise().search(
            query=query,
            search_depth="advanced",
            topic="general",
            max_results=4,
            include_answer="advanced",
            include_raw_content="text",
            auto_parameters=True,
        )

        sources = [
            SearchSource(
                title=result.get("title", "Untitled source"),
                url=result.get("url", ""),
                snippet=result.get("content", "")[:280],
                provider="tavily",
            )
            for result in response.get("results", [])[:4]
        ]
        answer = response.get("answer") or "No synthesized answer returned."
        summary = truncate_words(answer, 38)
        fact_lines = [answer]
        for source in sources[:3]:
            fact_lines.append(f"{source.title}: {source.snippet}")

        return ResearchUpdate(
            provider="tavily",
            query=query,
            search_queries=[query],
            summary=summary,
            fact_context="\n".join(fact_lines),
            sources=sources,
        )

    async def plan_follow_up_search(
        self,
        topic: str,
        history: list[dict],
        human_interrupt: str | None,
    ) -> SearchPlan:
        context = build_recent_context(history, 6) or "No recent exchange."
        try:
            response = await self._llm_or_raise().chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": PLAN_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"Topic: {topic}\n\n"
                            f"Recent exchange:\n{context}\n\n"
                            f"Audience input: {human_interrupt or 'None'}\n\n"
                            f"Known facts:\n{chr(10).join(self._fact_notes[-3:]) or 'None'}"
                        ),
                    },
                ],
                temperature=0.2,
                max_tokens=110,
            )
        except Exception:
            return SearchPlan()

        data = parse_json_blob(response.choices[0].message.content or "")
        return SearchPlan.model_validate(data or {})

    async def respond(
        self,
        topic: str,
        history: list[dict],
        human_interrupt: str | None,
    ) -> str:
        recent_context = build_recent_context(history, 6) or "No debate context yet."
        response = await self._llm_or_raise().chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": ARGUMENT_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Topic: {topic}\n\n"
                        f"Recent exchange:\n{recent_context}\n\n"
                        f"Audience input to address next: {human_interrupt or 'None'}\n\n"
                        f"Research notes:\n{chr(10).join(self._fact_notes[-3:]) or 'No research notes yet.'}\n\n"
                        f"Useful sources:\n{format_sources_for_prompt(self._sources)}"
                    ),
                },
            ],
            temperature=0.75,
            max_tokens=120,
        )
        return _response_text(response, "The pro case is stronger than that rebuttal made it sound.")

    def can_follow_up_search(self) -> bool:
        return self._follow_up_searches < 2

    def note_follow_up_search(self) -> None:
        self._follow_up_searches += 1
