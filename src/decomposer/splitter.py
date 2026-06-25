from __future__ import annotations

import re
from typing import Callable, List, Optional, Tuple

from .models import AgentType, ParsedRequest, Subtask
from .patterns import CLAUSE_SPLIT_PATTERN, COMPOUND_AND_PATTERN, COMPOUND_COMMA_PATTERN

AgentMatcher = Callable[[str], Tuple[Optional[AgentType], List[str]]]


class SubtaskSplitter:
    """
    Step 2 — Split the request into discrete, atomic subtasks.

    Each subtask should be small enough for one agent, e.g.:
      "Fetch 10 papers"      → one Retriever subtask
      "Extract key points"   → one Analyzer subtask
      "Generate report"      → one Writer subtask
    """

    def __init__(self, agent_matcher: AgentMatcher | None = None) -> None:
        self._agent_matcher = agent_matcher

    def split(self, parsed: ParsedRequest) -> List[Subtask]:
        """Split a parsed request into an ordered list of atomic subtasks."""
        if not parsed.normalized:
            return []

        clauses = self._split_clauses(parsed.normalized)
        subtasks: List[Subtask] = []

        for clause in clauses:
            for atomic in self._atomize_clause(clause):
                description = self._clean_fragment(atomic)
                if description:
                    subtasks.append(
                        Subtask(description=description, source_clause=clause)
                    )

        return subtasks

    def _atomize_clause(self, clause: str) -> List[str]:
        """Recursively split a clause until each part is one atomic subtask."""
        parts = self._split_compound_clause(clause, COMPOUND_AND_PATTERN)
        atomized: List[str] = []
        for part in parts:
            atomized.extend(self._split_compound_clause(part, COMPOUND_COMMA_PATTERN))
        return atomized or [clause]

    def _split_clauses(self, request: str) -> List[str]:
        """Split on sentence boundaries and step connectors."""
        parts = CLAUSE_SPLIT_PATTERN.split(request)
        clauses = [part.strip(" ,;.") for part in parts if part and part.strip(" ,;.")]
        return clauses or [request.strip()]

    def _split_compound_clause(self, clause: str, pattern: re.Pattern[str]) -> List[str]:
        """
        Split on a delimiter (and / comma) when each side maps to a different agent.

        Example: "Fetch 10 papers, extract key points, and generate a report"
          → ["Fetch 10 papers", "extract key points", "generate a report"]
        """
        if self._agent_matcher is None:
            return [clause]

        parts = pattern.split(clause)
        if len(parts) <= 1:
            return [clause]

        agents = [self._agent_matcher(part.strip())[0] for part in parts]
        if None in agents or len(set(agents)) <= 1:
            return [clause]

        return [part.strip() for part in parts if part.strip()]

    @staticmethod
    def _clean_fragment(text: str) -> str:
        """Remove step connectors left over from splitting."""
        cleaned = re.sub(r"^\s*then\s+", "", text, flags=re.IGNORECASE)
        return cleaned.strip(" ,;.")
