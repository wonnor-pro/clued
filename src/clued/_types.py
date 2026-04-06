from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ClueRecord:
    """A single error context entry."""

    msg: str
    kv: frozenset[tuple[str, Any]]
    filename: str
    lineno: int
