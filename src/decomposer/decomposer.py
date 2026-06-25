from __future__ import annotations

from .assigner import AgentAssigner
from .models import DecomposedTask
from .parser import RequestParser
from .splitter import SubtaskSplitter


class TaskDecomposer:
    """
    Orchestrates the three decomposition stages:

      1. Parse   — accept and normalize the user request string
      2. Split   — break into atomic subtasks (one agent each)
      3. Assign  — map each subtask to Retriever, Analyzer, or Writer

    Designed for simple rule-based parsing first; NLP backends can replace
    ``AgentAssigner.match_agent`` without changing the pipeline shape.
    """

    def __init__(
        self,
        parser: RequestParser | None = None,
        assigner: AgentAssigner | None = None,
    ) -> None:
        self.parser = parser or RequestParser()
        self.assigner = assigner or AgentAssigner(self.parser)
        self.splitter = SubtaskSplitter(agent_matcher=self.assigner.match_agent)

    def decompose(self, request: str) -> DecomposedTask:
        """Decompose a complex user request into an ordered agent execution plan."""
        parsed = self.parser.parse(request)
        subtasks = self.splitter.split(parsed)
        steps = self.assigner.assign(subtasks, fallback_request=parsed.normalized)

        return DecomposedTask(
            original_request=parsed.original,
            subtasks=subtasks,
            steps=steps,
        )
