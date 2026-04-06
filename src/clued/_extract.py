from typing import Any, cast

from clued._core import ClueHandle, _clue_stack
from clued._types import ClueRecord


def get_clues(exc: BaseException) -> list[ClueRecord]:
    """Return structured clue list from exception."""
    return cast(list[ClueRecord], getattr(exc, "__clues__", []))


def get_clue_dict(exc: BaseException) -> dict[str, Any]:
    """Return flat merged kv dict. Inner clues override outer."""
    result: dict[str, Any] = {}
    for c in reversed(get_clues(exc)):  # outer first, inner overrides
        result.update(c.kv)
    return result


def current_clues() -> tuple[ClueHandle, ...]:
    """Return active clue stack from ContextVar. For logging integration."""
    return _clue_stack.get()
