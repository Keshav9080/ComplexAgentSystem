from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from decomposer.models import AgentType

from .base import AgentError, BaseAgent


class WriterAgent(BaseAgent):
    """Generates structured output from analyzed data."""

    agent_type = AgentType.WRITER

    def __init__(
        self,
        latency_seconds: float = 0.05,
        should_fail: bool = False,
    ) -> None:
        self.latency_seconds = latency_seconds
        self.should_fail = should_fail

    async def run(self, payload: Any) -> Dict[str, Any]:
        analyzed_items: List[Dict[str, Any]] = payload["analyzed_items"]
        request: str = payload.get("request", "")

        if self.should_fail:
            raise AgentError("Writer failed while generating the final report")

        await asyncio.sleep(self.latency_seconds)
        return {
            "title": "Research Report",
            "request": request,
            "paper_count": len(analyzed_items),
            "sections": analyzed_items,
            "status": "ok",
        }
