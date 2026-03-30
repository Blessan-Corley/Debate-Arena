from __future__ import annotations

import asyncio
import logging
import re
from typing import AsyncGenerator

from agents.crowd import CrowdAgent
from agents.host import HostAgent
from agents.judge import JudgeAgent
from agents.pro import ProAgent
from agents.con import ConAgent
from config import Settings
from models import DebateEvent, ResearchUpdate
from storage import DebateStore


MAX_JUDGE_INTERRUPTS = 2

# debate_id -> asyncio.Queue for human interrupts
active_debates: dict[str, asyncio.Queue[str]] = {}
logger = logging.getLogger(__name__)


def drain_interrupts(queue: asyncio.Queue[str]) -> list[str]:
    messages: list[str] = []
    while True:
        try:
            messages.append(queue.get_nowait())
        except asyncio.QueueEmpty:
            return messages


def should_request_verdict(
    exchange_count: int,
    min_exchanges: int,
    max_exchanges: int,
    judge_signaled_end: bool,
) -> bool:
    if exchange_count < min_exchanges:
        return False
    if exchange_count >= max_exchanges:
        return True
    return judge_signaled_end


def should_consider_crowd(history: list[dict]) -> bool:
    recent_visible = [
        item
        for item in history
        if item.get("type") not in {"thinking", "search_started", "search_complete", "system_error"}
    ][-2:]
    return not any(item.get("type") == "crowd_reaction" for item in recent_visible)


def _winner_from_verdict(verdict: str) -> str | None:
    lowered = verdict.lower()
    if "winner: pro" in lowered or "pro wins" in lowered:
        return "pro"
    if "winner: con" in lowered or "con wins" in lowered:
        return "con"
    return None


def _search_metadata(update: ResearchUpdate) -> dict:
    return {
        "provider": update.provider,
        "query": update.query,
        "search_queries": update.search_queries,
        "sources": [source.model_dump() for source in update.sources],
        "summary": update.summary,
    }


async def run_debate(
    topic: str,
    min_exchanges: int,
    store: DebateStore,
    settings: Settings,
) -> AsyncGenerator[DebateEvent, None]:
    models = {
        "host": settings.host_model,
        "pro": settings.pro_model,
        "con": settings.con_model,
        "crowd": settings.crowd_model,
        "judge": settings.judge_model,
    }
    debate_id = await store.create_debate(topic, min_exchanges, models)
    interrupt_queue: asyncio.Queue[str] = asyncio.Queue()
    active_debates[debate_id] = interrupt_queue

    host = HostAgent(settings)
    pro = ProAgent(settings)
    con = ConAgent(settings)
    crowd = CrowdAgent(settings)
    judge = JudgeAgent(settings)

    history: list[dict] = []
    status = "failed"
    winner: str | None = None
    max_exchanges = min(min_exchanges + 2, 8)

    async def emit(
        *,
        agent: str,
        event_type: str,
        message: str,
        metadata: dict | None = None,
        persist: bool = True,
        visible: bool = True,
    ) -> DebateEvent:
        event = DebateEvent(
            debate_id=debate_id,
            agent=agent,
            type=event_type,
            message=message,
            metadata=metadata or {},
        )
        if visible:
            history.append(event.model_dump())
        if persist:
            await store.append_message(debate_id, event.model_dump())
        return event

    async def emit_human_interrupts(messages: list[str]) -> list[DebateEvent]:
        emitted = []
        for text in messages:
            emitted.append(
                await emit(
                    agent="human",
                    event_type="human",
                    message=text,
                    metadata={},
                )
            )
        return emitted

    try:
        yield DebateEvent(
            debate_id=debate_id,
            agent="system",
            type="debate_start",
            message="Debate started.",
            metadata={"topic": topic, "debate_id": debate_id},
        )

        yield DebateEvent(
            debate_id=debate_id,
            agent="host",
            type="thinking",
            message="Gopinath is taking the stage.",
        )
        intro = await host.introduce(topic)
        yield await emit(agent="host", event_type="host_intro", message=intro)

        yield await emit(
            agent="pro",
            event_type="search_started",
            message="Blessan is pulling live support evidence.",
            metadata={"provider": "tavily"},
        )
        pro_research = await pro.initial_research(topic)
        yield await emit(
            agent="pro",
            event_type="search_complete",
            message=pro_research.summary,
            metadata=_search_metadata(pro_research),
        )

        yield await emit(
            agent="con",
            event_type="search_started",
            message="Pranav is grounding the counter-case with live search.",
            metadata={"provider": "google-search"},
        )
        con_research = await con.initial_research(topic)
        yield await emit(
            agent="con",
            event_type="search_complete",
            message=con_research.summary,
            metadata=_search_metadata(con_research),
        )

        exchanges_completed = 0
        judge_interruptions = 0

        while exchanges_completed < max_exchanges:
            queued = drain_interrupts(interrupt_queue)
            if queued:
                for event in await emit_human_interrupts(queued):
                    yield event
            latest_human = queued[-1] if queued else None

            if pro.can_follow_up_search() and history:
                pro_plan = await pro.plan_follow_up_search(topic, history, latest_human)
                if pro_plan.needs_search and pro_plan.query:
                    yield await emit(
                        agent="pro",
                        event_type="search_started",
                        message="Blessan is checking a live factual counter.",
                        metadata={"provider": "tavily", "query": pro_plan.query, "reason": pro_plan.reason},
                    )
                    pro_update = await pro.run_search(pro_plan.query[:180])
                    pro.apply_research(pro_update)
                    pro.note_follow_up_search()
                    yield await emit(
                        agent="pro",
                        event_type="search_complete",
                        message=pro_update.summary,
                        metadata=_search_metadata(pro_update),
                    )

            yield DebateEvent(
                debate_id=debate_id,
                agent="pro",
                type="thinking",
                message="Blessan is shaping the next point.",
            )
            pro_message = await pro.respond(topic, history, latest_human)
            yield await emit(
                agent="pro",
                event_type="argument",
                message=pro_message,
                metadata={"word_count": len(re.findall(r"\S+", pro_message))},
            )

            pro_decision = await judge.evaluate_turn(
                topic=topic,
                history=history,
                exchange_count=exchanges_completed,
                interrupts_used=judge_interruptions,
                min_exchanges=min_exchanges,
            )
            pro_reaction = await crowd.maybe_react(topic, history) if should_consider_crowd(history) else None
            if (
                pro_decision.should_interrupt
                and judge_interruptions < MAX_JUDGE_INTERRUPTS
                and pro_decision.interrupt_message
            ):
                judge_interruptions += 1
                yield await emit(
                    agent="judge",
                    event_type="judge_interrupt",
                    message=pro_decision.interrupt_message,
                    metadata={"reason": pro_decision.reason},
                )

            if pro_reaction and pro_reaction.react and pro_reaction.message:
                yield await emit(
                    agent="crowd",
                    event_type="crowd_reaction",
                    message=pro_reaction.message,
                )

            queued = drain_interrupts(interrupt_queue)
            if queued:
                for event in await emit_human_interrupts(queued):
                    yield event
            latest_human = queued[-1] if queued else None

            if con.can_follow_up_search() and history:
                con_plan = await con.plan_follow_up_search(topic, history, latest_human)
                if con_plan.needs_search and con_plan.query:
                    yield await emit(
                        agent="con",
                        event_type="search_started",
                        message="Pranav is checking the factual record.",
                        metadata={"provider": "google-search", "query": con_plan.query, "reason": con_plan.reason},
                    )
                    con_update = await con.run_grounded_research(con_plan.query[:180])
                    con.apply_research(con_update)
                    con.note_follow_up_search()
                    yield await emit(
                        agent="con",
                        event_type="search_complete",
                        message=con_update.summary,
                        metadata=_search_metadata(con_update),
                    )

            yield DebateEvent(
                debate_id=debate_id,
                agent="con",
                type="thinking",
                message="Pranav is preparing the rebuttal.",
            )
            con_message = await con.respond(topic, history, latest_human)
            yield await emit(
                agent="con",
                event_type="argument",
                message=con_message,
                metadata={"word_count": len(re.findall(r"\S+", con_message))},
            )

            con_decision = await judge.evaluate_turn(
                topic=topic,
                history=history,
                exchange_count=exchanges_completed + 1,
                interrupts_used=judge_interruptions,
                min_exchanges=min_exchanges,
            )
            con_reaction = await crowd.maybe_react(topic, history) if should_consider_crowd(history) else None
            if (
                con_decision.should_interrupt
                and judge_interruptions < MAX_JUDGE_INTERRUPTS
                and con_decision.interrupt_message
            ):
                judge_interruptions += 1
                yield await emit(
                    agent="judge",
                    event_type="judge_interrupt",
                    message=con_decision.interrupt_message,
                    metadata={"reason": con_decision.reason},
                )

            if con_reaction and con_reaction.react and con_reaction.message:
                yield await emit(
                    agent="crowd",
                    event_type="crowd_reaction",
                    message=con_reaction.message,
                )

            exchanges_completed += 1
            if should_request_verdict(
                exchange_count=exchanges_completed,
                min_exchanges=min_exchanges,
                max_exchanges=max_exchanges,
                judge_signaled_end=con_decision.should_end,
            ):
                break

        yield DebateEvent(
            debate_id=debate_id,
            agent="judge",
            type="thinking",
            message="Pradhakshini is preparing the verdict.",
        )
        verdict = await judge.final_verdict(topic, history)
        winner = _winner_from_verdict(verdict)
        yield await emit(
            agent="judge",
            event_type="judge_verdict",
            message=verdict,
            metadata={"winner": winner},
        )
        status = "completed"
        yield DebateEvent(
            debate_id=debate_id,
            agent="system",
            type="debate_end",
            message="Debate ended.",
            metadata={"winner": winner},
        )
    except Exception as exc:
        logger.exception("Debate %s failed while streaming topic %r", debate_id, topic)
        error_event = await emit(
            agent="system",
            event_type="system_error",
            message="The Arena hit an internal error while running this debate.",
            metadata={"error": str(exc)},
        )
        yield error_event
    finally:
        await store.finalize_debate(debate_id, winner=winner, status=status)
        active_debates.pop(debate_id, None)
