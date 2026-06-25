from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Set

from decomposer.models import AgentType

from .base import AgentError, BaseAgent


class AnalyzerAgent(BaseAgent):
    """Processes and interprets retrieved data."""

    agent_type = AgentType.ANALYZER

    def __init__(
        self,
        latency_seconds: float = 0.05,
        fail_on_batches: Optional[Set[int]] = None,
    ) -> None:
        self.latency_seconds = latency_seconds
        self.fail_on_batches = fail_on_batches or set()

    async def run(self, payload: Any) -> List[Dict[str, Any]]:
        batch_index = payload["batch_index"]
        papers: List[Dict[str, Any]] = payload["papers"]

        if batch_index in self.fail_on_batches:
            raise AgentError(f"Analyzer failed on batch {batch_index}")

        await asyncio.sleep(self.latency_seconds)
        return [
            {
                "paper_id": paper["id"],
                "key_points": [
                    f"Main finding for paper {paper['id']}",
                    f"Methodology summary for paper {paper['id']}",
                ],
                "status": "ok",
            }
            for paper in papers
        ]
