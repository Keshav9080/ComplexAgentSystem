from __future__ import annotations

from typing import Dict

from decomposer.models import AgentType

from .analyzer import AnalyzerAgent
from .base import BaseAgent
from .retriever import RetrieverAgent
from .writer import WriterAgent

AGENT_REGISTRY: Dict[AgentType, type[BaseAgent]] = {
    AgentType.RETRIEVER: RetrieverAgent,
    AgentType.ANALYZER: AnalyzerAgent,
    AgentType.WRITER: WriterAgent,
}
