from __future__ import annotations

import re
from typing import List

FETCH_COUNT_PATTERN = re.compile(r"\b(\d+)\s+papers?\b", re.IGNORECASE)
DEFAULT_FETCH_COUNT = 10


def parse_fetch_count(description: str, default: int = DEFAULT_FETCH_COUNT) -> int:
    """Extract item count from descriptions like 'Fetch 10 papers'."""
    match = FETCH_COUNT_PATTERN.search(description)
    if match:
        return max(1, int(match.group(1)))
    return default


def manual_batches(total_items: int, batch_size: int) -> List[List[int]]:
    """
    Split work into fixed-size manual batches.

    Example: 10 papers, batch_size=2 ->
      [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10]]
    """
    if total_items < 1:
        return []
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    batches: List[List[int]] = []
    for start in range(0, total_items, batch_size):
        batch = list(range(start + 1, min(start + batch_size, total_items) + 1))
        batches.append(batch)
    return batches
