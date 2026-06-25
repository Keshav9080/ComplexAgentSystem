from __future__ import annotations

from typing import AsyncIterator, Optional, Set

from decomposer import DecomposedTask, TaskDecomposer

from .executor import PipelineExecutor
from .models import StreamEvent


class AgentPipeline:
    """End-to-end entry point: decompose a request, then execute the async pipeline."""

    def __init__(
        self,
        batch_size: int = 2,
        retriever_fail_batches: Optional[Set[int]] = None,
        analyzer_fail_batches: Optional[Set[int]] = None,
        writer_should_fail: bool = False,
        decomposer: Optional[TaskDecomposer] = None,
    ) -> None:
        self.decomposer = decomposer or TaskDecomposer()
        self.executor = PipelineExecutor(
            batch_size=batch_size,
            retriever_fail_batches=retriever_fail_batches,
            analyzer_fail_batches=analyzer_fail_batches,
            writer_should_fail=writer_should_fail,
        )

    def decompose(self, request: str) -> DecomposedTask:
        return self.decomposer.decompose(request)

    async def run(self, request: str) -> AsyncIterator[StreamEvent]:
        plan = self.decompose(request)
        async for event in self.executor.run(plan):
            yield event
