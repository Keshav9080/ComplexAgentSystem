from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class AgentType(str, Enum):
    """Specialized agents in the execution pipeline."""

    RETRIEVER = "retriever"
    ANALYZER = "analyzer"
    WRITER = "writer"


@dataclass(frozen=True)
class ParsedRequest:
    """Normalized user input ready for decomposition."""

    original: str
    normalized: str


@dataclass(frozen=True)
class Subtask:
    """One atomic unit of work — small enough for a single agent."""

    description: str
    source_clause: str = ""


@dataclass(frozen=True)
class TaskStep:
    """A subtask assigned to one specialized agent."""

    order: int
    agent: AgentType
    description: str
    matched_keywords: tuple[str, ...] = ()


@dataclass
class DecomposedTask:
    """Full execution plan produced from a complex user request."""

    original_request: str
    subtasks: List[Subtask] = field(default_factory=list)
    steps: List[TaskStep] = field(default_factory=list)

    @property
    def agent_sequence(self) -> List[AgentType]:
        return [step.agent for step in self.steps]
