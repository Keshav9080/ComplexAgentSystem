from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from decomposer.models import AgentType, DecomposedTask


class StreamEventType(str, Enum):
    BATCH_START = "batch_start"
    PARTIAL = "partial"
    BATCH_FAILED = "batch_failed"
    FINAL = "final"
    PIPELINE_FAILED = "pipeline_failed"


@dataclass(frozen=True)
class StreamEvent:
    """Partial or final output streamed to the caller."""

    event_type: StreamEventType
    agent: AgentType
    message: str
    data: Any = None
    batch_index: Optional[int] = None
    recovered: bool = False


@dataclass
class AgentOutcome:
    """Result of a single agent invocation."""

    agent: AgentType
    success: bool
    data: Any
    error: Optional[str] = None
    used_fallback: bool = False


@dataclass
class BatchResult:
    """Outcome of processing one manual batch through retrieve + analyze."""

    batch_index: int
    paper_ids: List[int]
    retrieve: AgentOutcome
    analyze: AgentOutcome


@dataclass
class PipelineContext:
    """Shared state carried through the execution pipeline."""

    plan: DecomposedTask
    batch_size: int
    total_items: int
    batches: List[List[int]] = field(default_factory=list)
    batch_results: List[BatchResult] = field(default_factory=list)
    analyzed_items: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def completed_batches(self) -> int:
        return len(self.batch_results)
