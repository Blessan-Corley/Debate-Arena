from __future__ import annotations

from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel

from agents.common import (
    build_recent_context,
    format_sources_for_prompt,
    parse_json_blob,
    truncate_words,
)
from config import Settings
from models import ResearchUpdate, SearchPlan, SearchSource


class _GeminiResearchResponse(BaseModel):
    summary: str
    fact_points: list[str]


PLAN_SCHEMA = SearchPlan.model_json_schema()


PLAN_PROMPT = """You are the Con debater's research planner.
Return JSON only with:
- needs_search: boolean
- query: string or null
- reason: string or null

Search only when a recent claim needs fresh evidence, a current example, or fact-checking."""

RESEARCH_PROMPT = """You are preparing the Con side's factual research brief.
Use Google Search grounding when useful.

Return this exact shape:
SUMMARY: one short paragraph
FACTS:
- fact one
- fact two
- fact three

Rules:
- Focus on evidence that challenges or complicates the motion
- Keep the brief concise and specific"""

ARGUMENT_PROMPT = """You are PRANAV, the Con debater on THE ARENA.
You argue against the motion with precise, cold clarity.

Voice:
- Analytical, controlled, slightly cutting
- Comfortable disagreeing with the audience if needed
- Never ranty, never generic

Rules:
- 50 to 80 words
- Attack the actual weak point in the latest Pro or Human move
- Use evidence cleanly, without sounding like a search result
- End with a line that leaves the Pro case looking thinner than it arrived"""


def _response_text(response, fallback: str) -> str:
    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()
    return fallback


def _fallback_fact_points(text: str) -> list[str]:
    lines = [
        line.strip(" -*•\t")
        for line in text.splitlines()
        if line.strip()
    ]
    return [line for line in lines if len(line) > 18][:4]


def _coerce_research_payload(text: str) -> _GeminiResearchResponse:
    cleaned_text = text.strip()
    upper_text = cleaned_text.upper()
    if "SUMMARY:" in upper_text:
        summary_start = upper_text.find("SUMMARY:")
        facts_start = upper_text.find("FACTS:")
        if facts_start > summary_start:
            summary = cleaned_text[summary_start + len("SUMMARY:"):facts_start].strip()
            facts_block = cleaned_text[facts_start + len("FACTS:"):].strip()
            fact_points = _fallback_fact_points(facts_block)
            if summary and fact_points:
                return _GeminiResearchResponse(
                    summary=truncate_words(summary, 38),
                    fact_points=fact_points[:5],
                )

    data = parse_json_blob(text)
    if data:
        summary = str(data.get("summary") or "").strip()
        raw_fact_points = data.get("fact_points") or []
        fact_points = [
            str(point).strip()
            for point in raw_fact_points
            if str(point).strip()
        ]
        if summary and fact_points:
            return _GeminiResearchResponse(summary=summary, fact_points=fact_points[:5])

    cleaned = " ".join(text.split()).strip()
    summary = truncate_words(cleaned or "No grounded research summary returned.", 38)
    fact_points = _fallback_fact_points(text)
    if not fact_points and cleaned:
        fact_points = [summary]
    return _GeminiResearchResponse(summary=summary, fact_points=fact_points[:5])


def _coerce_search_plan_response(response: Any) -> SearchPlan:
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, SearchPlan):
        return parsed
    if isinstance(parsed, dict):
        return SearchPlan.model_validate(parsed)

    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        data = parse_json_blob(text)
        if data:
            return SearchPlan.model_validate(data)

    return SearchPlan()


class ConAgent:
    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.gemini_api_key
        self._model = settings.con_model
        self._client: genai.Client | None = None
        self._fact_notes: list[str] = []
        self._sources: list[SearchSource] = []
        self._follow_up_searches = 0

    def _client_or_raise(self) -> genai.Client:
        if not self._api_key:
            raise RuntimeError("Missing GEMINI_API_KEY for con agent")
        if self._client is None:
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def apply_research(self, update: ResearchUpdate) -> None:
        self._fact_notes.append(update.fact_context)
        self._fact_notes = self._fact_notes[-6:]
        self._sources.extend(update.sources)
        self._sources = self._sources[-12:]

    async def initial_research(self, topic: str) -> ResearchUpdate:
        update = await self.run_grounded_research(
            f"Research evidence and current examples arguing against: {topic}"
        )
        self.apply_research(update)
        return update

    async def run_grounded_research(self, query: str) -> ResearchUpdate:
        response = await self._client_or_raise().aio.models.generate_content(
            model=self._model,
            contents=query,
            config=types.GenerateContentConfig(
                system_instruction=RESEARCH_PROMPT,
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.3,
                max_output_tokens=320,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        structured = _coerce_research_payload(response.text)
        metadata = getattr(response.candidates[0], "grounding_metadata", None) if response.candidates else None
        raw_queries = getattr(metadata, "web_search_queries", None) if metadata else None
        search_queries = list(raw_queries or [])
        grounding_chunks = getattr(metadata, "grounding_chunks", None) if metadata else None

        sources: list[SearchSource] = []
        for chunk in grounding_chunks or []:
            web = getattr(chunk, "web", None)
            if not web:
                continue
            title = getattr(web, "title", None) or "Google Search Result"
            url = getattr(web, "uri", None) or getattr(web, "url", None) or ""
            snippet = structured.summary[:280]
            sources.append(
                SearchSource(
                    title=title,
                    url=url,
                    snippet=snippet,
                    provider="google-search",
                )
            )

        fact_context = "\n".join(structured.fact_points)
        return ResearchUpdate(
            provider="google-search",
            query=query,
            search_queries=search_queries,
            summary=truncate_words(structured.summary, 38),
            fact_context=fact_context,
            sources=sources[:4],
        )

    async def plan_follow_up_search(
        self,
        topic: str,
        history: list[dict],
        human_interrupt: str | None,
    ) -> SearchPlan:
        recent_context = build_recent_context(history, 6) or "No recent exchange."
        response = await self._client_or_raise().aio.models.generate_content(
            model=self._model,
            contents=(
                f"Topic: {topic}\n\n"
                f"Recent exchange:\n{recent_context}\n\n"
                f"Audience input: {human_interrupt or 'None'}\n\n"
                f"Known facts:\n{chr(10).join(self._fact_notes[-3:]) or 'None'}"
            ),
            config=types.GenerateContentConfig(
                system_instruction=PLAN_PROMPT,
                response_mime_type="application/json",
                response_json_schema=PLAN_SCHEMA,
                temperature=0.2,
                max_output_tokens=100,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        return _coerce_search_plan_response(response)

    async def respond(
        self,
        topic: str,
        history: list[dict],
        human_interrupt: str | None,
    ) -> str:
        recent_context = build_recent_context(history, 6) or "No debate context yet."
        response = await self._client_or_raise().aio.models.generate_content(
            model=self._model,
            contents=(
                f"Topic: {topic}\n\n"
                f"Recent exchange:\n{recent_context}\n\n"
                f"Audience input to address next: {human_interrupt or 'None'}\n\n"
                f"Research notes:\n{chr(10).join(self._fact_notes[-3:]) or 'No research notes yet.'}\n\n"
                f"Useful sources:\n{format_sources_for_prompt(self._sources)}"
            ),
            config=types.GenerateContentConfig(
                system_instruction=ARGUMENT_PROMPT,
                temperature=0.65,
                max_output_tokens=120,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        return _response_text(response, "That rebuttal sounds firmer than the evidence beneath it.")

    def can_follow_up_search(self) -> bool:
        return self._follow_up_searches < 2

    def note_follow_up_search(self) -> None:
        self._follow_up_searches += 1
