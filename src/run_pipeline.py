"""Run the async agent pipeline with batching and failure handling."""

from __future__ import annotations

import asyncio

from pipeline import AgentPipeline


async def run_demo(title: str, pipeline: AgentPipeline, request: str) -> None:
    print(f"=== {title} ===")
    print(f"Request: {request}\n")

    plan = pipeline.decompose(request)
    print("Decomposed steps:")
    for step in plan.steps:
        print(f"  {step.order}. [{step.agent.value}] {step.description}")
    print()

    async for event in pipeline.executor.run(plan):
        flag = " (recovered)" if event.recovered else ""
        batch = f" [batch {event.batch_index}]" if event.batch_index is not None else ""
        print(f"  [{event.event_type.value}]{batch}{flag} {event.message}")

    print()


async def main() -> None:
    request = "Fetch 10 papers, extract key points, and generate a report."

    print("Demo 1: Happy path (batch_size=2, 10 papers -> 5 batches)\n")
    happy = AgentPipeline(batch_size=2)
    await run_demo("Happy path", happy, request)

    print("Demo 2: Retriever failure on batch 1 (papers 3-4) — pipeline continues\n")
    with_failure = AgentPipeline(batch_size=2, retriever_fail_batches={1})
    await run_demo("Failure recovery", with_failure, request)


if __name__ == "__main__":
    asyncio.run(main())
