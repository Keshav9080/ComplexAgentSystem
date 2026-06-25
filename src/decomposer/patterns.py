from __future__ import annotations

import re
from typing import Dict, Iterable, List, Pattern, Tuple

from .models import AgentType

# Keyword → agent mapping (simple verb/pattern matching; NLP can replace this later).
AGENT_KEYWORDS: Dict[AgentType, Tuple[str, ...]] = {
    AgentType.RETRIEVER: (
        "fetch",
        "retrieve",
        "get",
        "load",
        "search",
        "find",
        "collect",
        "download",
        "pull",
        "query",
        "lookup",
        "read",
    ),
    AgentType.ANALYZER: (
        "analyze",
        "analyse",
        "examine",
        "evaluate",
        "assess",
        "interpret",
        "process",
        "compare",
        "review",
        "inspect",
        "summarize",
        "summarise",
        "extract",
        "identify",
        "classify",
    ),
    AgentType.WRITER: (
        "write",
        "generate",
        "create",
        "compose",
        "draft",
        "produce",
        "format",
        "report",
        "document",
        "output",
        "render",
    ),
}

AGENT_ROLES: Dict[AgentType, str] = {
    AgentType.RETRIEVER: "data fetching tasks",
    AgentType.ANALYZER: "processing and interpretation tasks",
    AgentType.WRITER: "formatting and output generation tasks",
}

AGENT_PRIORITY: Tuple[AgentType, ...] = (
    AgentType.RETRIEVER,
    AgentType.ANALYZER,
    AgentType.WRITER,
)

CLAUSE_SPLIT_PATTERN = re.compile(
    r"""
    \s*(?:\d+[\).\]]\s*)
    | \s*;\s*
    | \s*\.\s+
    | \s*\n+
    | \s+\band\s+then\s+
    | \s+\bthen\s+
    | \s*,\s*and\s+
    """,
    re.IGNORECASE | re.VERBOSE,
)

COMPOUND_AND_PATTERN = re.compile(r"\s+\band\s+", re.IGNORECASE)
COMPOUND_COMMA_PATTERN = re.compile(r"\s*,\s+")
WORD_PATTERN = re.compile(r"\b[a-z][a-z'-]*\b", re.IGNORECASE)


def compile_keyword_patterns() -> Dict[AgentType, List[Pattern[str]]]:
    return {
        agent: [
            re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
            for keyword in keywords
        ]
        for agent, keywords in AGENT_KEYWORDS.items()
    }


def find_matched_keywords(
    text: str,
    keywords: Tuple[str, ...],
    patterns: Iterable[Pattern[str]],
) -> List[str]:
    return [
        keyword
        for keyword, pattern in zip(keywords, patterns)
        if pattern.search(text)
    ]
