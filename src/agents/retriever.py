from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Set

from decomposer.models import AgentType

from .base import AgentError, BaseAgent


class RetrieverAgent(BaseAgent):
    """Fetches input data in manual batches."""

    agent_type = AgentType.RETRIEVER

    def __init__(
        self,
        latency_seconds: float = 0.05,
        fail_on_batches: Optional[Set[int]] = None,
    ) -> None:
        self.latency_seconds = latency_seconds
        self.fail_on_batches = fail_on_batches or set()

    async def run(self, payload: Any) -> List[Dict[str, Any]]:
        batch_index = payload["batch_index"]
        paper_ids: List[int] = payload["paper_ids"]

        if batch_index in self.fail_on_batches:
            raise AgentError(
                f"Retriever failed on batch {batch_index} "
                f"(papers {paper_ids[0]}-{paper_ids[-1]})"
            )

        await asyncio.sleep(self.latency_seconds)
        return [
            {
                "id": paper_id,
                "title": f"Paper {paper_id}: Sample Research Title",
                "source": "live",
                "status": "ok",
            }
            for paper_id in paper_ids
        ]
