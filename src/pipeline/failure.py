from __future__ import annotations

from typing import Any, Callable, Dict, List, TypeVar

from decomposer.models import AgentType

from .models import AgentOutcome

T = TypeVar("T")


def retriever_fallback(paper_ids: List[int], error: Exception) -> List[Dict[str, Any]]:
    """Use cached metadata when live fetch fails."""
    return [
        {
            "id": paper_id,
            "title": f"Paper {paper_id} (cached fallback)",
            "source": "cache",
            "status": "fallback",
        }
        for paper_id in paper_ids
    ]


def analyzer_fallback(
    papers: List[Dict[str, Any]],
    error: Exception,
) -> List[Dict[str, Any]]:
    """Produce minimal key points when analysis fails."""
    return [
        {
            "paper_id": paper["id"],
            "key_points": [f"Unable to analyze: {error}"],
            "status": "fallback",
        }
        for paper in papers
    ]


def writer_fallback(
    analyzed_items: List[Dict[str, Any]],
    error: Exception,
) -> Dict[str, Any]:
    """Return a partial report instead of crashing the pipeline."""
    return {
        "title": "Partial Report (writer fallback)",
        "sections": analyzed_items,
        "note": f"Writer failed: {error}. Returning collected analysis only.",
        "status": "fallback",
    }


FALLBACKS: Dict[AgentType, Callable[..., Any]] = {
    AgentType.RETRIEVER: retriever_fallback,
    AgentType.ANALYZER: analyzer_fallback,
    AgentType.WRITER: writer_fallback,
}


async def run_agent_safe(
    agent: AgentType,
    execute: Callable[[], Any],
    fallback: Callable[[Exception], Any],
) -> AgentOutcome:
    """Wrap agent execution so one failure does not break the pipeline."""
    try:
        data = await execute()
        return AgentOutcome(agent=agent, success=True, data=data)
    except Exception as exc:
        recovered = fallback(exc)
        return AgentOutcome(
            agent=agent,
            success=False,
            data=recovered,
            error=str(exc),
            used_fallback=True,
        )
