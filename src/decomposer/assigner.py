from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from .models import AgentType, Subtask, TaskStep
from .patterns import (
    AGENT_KEYWORDS,
    AGENT_PRIORITY,
    AGENT_ROLES,
    compile_keyword_patterns,
    find_matched_keywords,
)
from .parser import RequestParser


class AgentAssigner:
    """
    Step 3 — Assign each atomic subtask to a specialized agent.

    Mapping:
      Retriever → data fetching tasks   (fetch, retrieve, get, …)
      Analyzer  → processing tasks      (analyze, extract, summarize, …)
      Writer    → formatting tasks      (write, generate, report, …)
    """

    DEFAULT_PIPELINE: Sequence[Tuple[AgentType, str]] = (
        (AgentType.RETRIEVER, "Retrieve input for: {request}"),
        (AgentType.ANALYZER, "Analyze data for: {request}"),
        (AgentType.WRITER, "Write output for: {request}"),
    )

    def __init__(self, parser: RequestParser | None = None) -> None:
        self._parser = parser or RequestParser()
        self._keyword_patterns = compile_keyword_patterns()

    def assign(self, subtasks: List[Subtask], fallback_request: str = "") -> List[TaskStep]:
        """Map subtasks to agents and return ordered execution steps."""
        if not subtasks:
            return self._default_pipeline(fallback_request)

        steps: List[TaskStep] = []
        for subtask in subtasks:
            agent, keywords = self.match_agent(subtask.description)
            if agent is None:
                continue
            steps.append(
                TaskStep(
                    order=len(steps) + 1,
                    agent=agent,
                    description=subtask.description,
                    matched_keywords=tuple(keywords),
                )
            )

        if not steps and fallback_request:
            return self._default_pipeline(fallback_request)

        return self._renumber(steps)

    def match_agent(self, text: str) -> Tuple[Optional[AgentType], List[str]]:
        """
        Identify keywords/patterns in a subtask and return the best-fit agent.

        Override this method to plug in NLP-based intent classification later.
        """
        matches: Dict[AgentType, List[str]] = {}

        for agent, patterns in self._keyword_patterns.items():
            hits = find_matched_keywords(text, AGENT_KEYWORDS[agent], patterns)
            if hits:
                matches[agent] = hits

        if not matches:
            inferred = self._infer_from_leading_verb(text)
            if inferred is None:
                return None, []
            return inferred, [inferred.value]

        chosen = min(matches.keys(), key=lambda agent: AGENT_PRIORITY.index(agent))
        return chosen, matches[chosen]

    def agent_role(self, agent: AgentType) -> str:
        """Human-readable description of what this agent handles."""
        return AGENT_ROLES[agent]

    def _infer_from_leading_verb(self, text: str) -> Optional[AgentType]:
        verb = self._parser.leading_verb(text)
        if verb is None:
            return None

        for agent, keywords in AGENT_KEYWORDS.items():
            if any(verb == keyword or verb.startswith(keyword) for keyword in keywords):
                return agent
        return None

    def _default_pipeline(self, request: str) -> List[TaskStep]:
        """When no keywords match, assume Retriever → Analyzer → Writer."""
        return [
            TaskStep(
                order=index,
                agent=agent,
                description=description.format(request=request),
                matched_keywords=(agent.value,),
            )
            for index, (agent, description) in enumerate(self.DEFAULT_PIPELINE, start=1)
        ]

    @staticmethod
    def _renumber(steps: List[TaskStep]) -> List[TaskStep]:
        return [
            TaskStep(
                order=index,
                agent=step.agent,
                description=step.description,
                matched_keywords=step.matched_keywords,
            )
            for index, step in enumerate(steps, start=1)
        ]
