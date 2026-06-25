from __future__ import annotations

from typing import AsyncIterator, Optional, Set

from decomposer.models import AgentType, DecomposedTask, TaskStep

from agents.analyzer import AnalyzerAgent
from agents.retriever import RetrieverAgent
from agents.writer import WriterAgent
from .batching import manual_batches, parse_fetch_count
from .failure import (
    analyzer_fallback,
    retriever_fallback,
    run_agent_safe,
    writer_fallback,
)
from .models import (
    BatchResult,
    PipelineContext,
    StreamEvent,
    StreamEventType,
)


class PipelineExecutor:
    """
    Async execution pipeline with manual batching, streaming, and failure handling.

    Retriever work is split into fixed-size batches (default 2 papers at a time).
    Each agent runs inside a safe wrapper; failures trigger fallbacks and the
    pipeline continues.
    """

    def __init__(
        self,
        batch_size: int = 2,
        retriever_fail_batches: Optional[Set[int]] = None,
        analyzer_fail_batches: Optional[Set[int]] = None,
        writer_should_fail: bool = False,
    ) -> None:
        self.batch_size = batch_size
        self.retriever = RetrieverAgent(fail_on_batches=retriever_fail_batches)
        self.analyzer = AnalyzerAgent(fail_on_batches=analyzer_fail_batches)
        self.writer = WriterAgent(should_fail=writer_should_fail)

    async def run(self, plan: DecomposedTask) -> AsyncIterator[StreamEvent]:
        context = self._build_context(plan)

        for batch_index, paper_ids in enumerate(context.batches):
            yield StreamEvent(
                event_type=StreamEventType.BATCH_START,
                agent=AgentType.RETRIEVER,
                message=f"Processing batch {batch_index + 1}/{len(context.batches)}: papers {paper_ids}",
                batch_index=batch_index,
            )

            retrieve_outcome = await run_agent_safe(
                AgentType.RETRIEVER,
                lambda: self.retriever.run(
                    {"batch_index": batch_index, "paper_ids": paper_ids}
                ),
                lambda exc: retriever_fallback(paper_ids, exc),
            )

            if retrieve_outcome.used_fallback:
                context.errors.append(retrieve_outcome.error or "Retriever fallback used")
                yield StreamEvent(
                    event_type=StreamEventType.BATCH_FAILED,
                    agent=AgentType.RETRIEVER,
                    message=f"Retriever failed on batch {batch_index}; using cache fallback",
                    data=retrieve_outcome.data,
                    batch_index=batch_index,
                    recovered=True,
                )

            analyze_outcome = await run_agent_safe(
                AgentType.ANALYZER,
                lambda: self.analyzer.run(
                    {
                        "batch_index": batch_index,
                        "papers": retrieve_outcome.data,
                    }
                ),
                lambda exc: analyzer_fallback(retrieve_outcome.data, exc),
            )

            if analyze_outcome.used_fallback:
                context.errors.append(analyze_outcome.error or "Analyzer fallback used")
                yield StreamEvent(
                    event_type=StreamEventType.BATCH_FAILED,
                    agent=AgentType.ANALYZER,
                    message=f"Analyzer failed on batch {batch_index}; using partial analysis",
                    data=analyze_outcome.data,
                    batch_index=batch_index,
                    recovered=True,
                )

            context.analyzed_items.extend(analyze_outcome.data)
            batch_result = BatchResult(
                batch_index=batch_index,
                paper_ids=paper_ids,
                retrieve=retrieve_outcome,
                analyze=analyze_outcome,
            )
            context.batch_results.append(batch_result)

            yield StreamEvent(
                event_type=StreamEventType.PARTIAL,
                agent=AgentType.ANALYZER,
                message=f"Completed batch {batch_index + 1}: {len(analyze_outcome.data)} analyses ready",
                data=analyze_outcome.data,
                batch_index=batch_index,
            )

        writer_outcome = await run_agent_safe(
            AgentType.WRITER,
            lambda: self.writer.run(
                {
                    "analyzed_items": context.analyzed_items,
                    "request": plan.original_request,
                }
            ),
            lambda exc: writer_fallback(context.analyzed_items, exc),
        )

        if writer_outcome.used_fallback:
            context.errors.append(writer_outcome.error or "Writer fallback used")
            yield StreamEvent(
                event_type=StreamEventType.PIPELINE_FAILED,
                agent=AgentType.WRITER,
                message="Writer failed; returning partial report",
                data=writer_outcome.data,
                recovered=True,
            )

        yield StreamEvent(
            event_type=StreamEventType.FINAL,
            agent=AgentType.WRITER,
            message="Pipeline complete",
            data=writer_outcome.data,
        )

    def _build_context(self, plan: DecomposedTask) -> PipelineContext:
        retriever_step = self._find_step(plan, AgentType.RETRIEVER)
        description = retriever_step.description if retriever_step else plan.original_request
        total_items = parse_fetch_count(description)
        batches = manual_batches(total_items, self.batch_size)

        return PipelineContext(
            plan=plan,
            batch_size=self.batch_size,
            total_items=total_items,
            batches=batches,
        )

    @staticmethod
    def _find_step(plan: DecomposedTask, agent: AgentType) -> Optional[TaskStep]:
        for step in plan.steps:
            if step.agent == agent:
                return step
        return None
