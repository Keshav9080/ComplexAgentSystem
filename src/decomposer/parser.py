from __future__ import annotations

from typing import Dict, List

from .models import AgentType, ParsedRequest
from .patterns import AGENT_KEYWORDS, compile_keyword_patterns, find_matched_keywords


class RequestParser:
    """
    Step 1 — Parse the input request.

    Accepts a raw string, normalizes it, and scans for action keywords/verbs.
    Uses simple token matching today; swap in NLP tokenization later if needed.
    """

    def __init__(self) -> None:
        self._keyword_patterns = compile_keyword_patterns()

    def parse(self, request: str) -> ParsedRequest:
        """Accept the user's request as a string and return a normalized form."""
        return ParsedRequest(original=request, normalized=request.strip())

    def identify_keywords(self, text: str) -> Dict[AgentType, List[str]]:
        """
        Scan text for known action patterns (fetch, analyze, summarize, write, …).

        Returns a mapping of agent type → matched keywords found in the text.
        """
        hits: Dict[AgentType, List[str]] = {}
        for agent, patterns in self._keyword_patterns.items():
            matched = find_matched_keywords(text, AGENT_KEYWORDS[agent], patterns)
            if matched:
                hits[agent] = matched
        return hits

    def leading_verb(self, clause: str) -> str | None:
        """Return the first word-like token, treated as a candidate verb."""
        from .patterns import WORD_PATTERN

        match = WORD_PATTERN.search(clause)
        return match.group(0).lower() if match else None
