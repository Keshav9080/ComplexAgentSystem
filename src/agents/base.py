from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from decomposer.models import AgentType


class AgentError(Exception):
    """Raised when an agent cannot complete its work."""


class BaseAgent(ABC):
    agent_type: AgentType

    @abstractmethod
    async def run(self, payload: Any) -> Any:
        """Execute the agent's task and return structured output."""
