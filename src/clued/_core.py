import sys
from collections.abc import Generator, Mapping
from contextlib import AbstractContextManager, contextmanager
from contextvars import ContextVar
from copy import deepcopy
from typing import Any, NamedTuple, final

from clued._types import ClueRecord

_clue_stack: ContextVar[tuple["ClueHandle", ...]] = ContextVar("clued_stack", default=())


@final
class CodeLocation(NamedTuple):
    filename: str
    lineno: int

    @property
    def code_path(self) -> str:
        return f"{self.filename}:{self.lineno}"


def _capture_loc(depth: int = 1) -> CodeLocation:
    """Capture the caller's location. ``depth=1`` is the direct caller of this function."""
    frame = sys._getframe(depth + 1)
    loc = CodeLocation(frame.f_code.co_filename, frame.f_lineno)
    del frame
    return loc


@final
class ClueHandle:
    """The object yielded by ``with clue(...) as handle``."""

    __slots__ = ("msg", "kv", "_original_msg", "_loc", "_refine_loc")

    def __init__(self, msg: str, kv: Mapping[str, Any], loc: CodeLocation) -> None:
        self.msg = msg
        self.kv: dict[str, Any] = dict(kv)
        self._original_msg = msg
        self._loc = loc
        self._refine_loc: CodeLocation | None = None

    def refine(self, msg: str | None = None, **kv: Any) -> None:
        """Update context in-place. ``None`` values delete the key."""
        self._refine_loc = _capture_loc(depth=1)

        if msg is not None:
            self.msg = msg

        for k, v in kv.items():
            if v is None:
                self.kv.pop(k, None)
            else:
                self.kv[k] = v

    def reset(self) -> None:
        """Restore to original msg, clear all kv, clear _refine_loc."""
        self.msg = self._original_msg
        self.kv.clear()
        self._refine_loc = None

    def _snapshot(self) -> tuple[str, dict[str, Any], CodeLocation]:
        """Return current (msg, kv copy, loc) for note building."""
        loc = self._refine_loc if self._refine_loc is not None else self._loc
        return self.msg, dict(self.kv), loc


def _format_note(msg: str, kv: dict[str, Any], loc: CodeLocation, depth: int) -> str:
    note = f"- Clue {depth}: {msg} [{', '.join(f'{k}={v!r}' for k, v in kv.items())}] ({loc.code_path})"
    return note


def clue(msg: str, **kv: Any) -> AbstractContextManager[ClueHandle]:
    """Context manager that attaches structured context to any exception raised within this block."""
    # Capture caller location here — this function is called directly from user code.
    loc = _capture_loc(depth=1)
    return _clue_cm(msg, kv, loc)


@contextmanager
def _clue_cm(msg: str, kv: Mapping[str, Any], loc: CodeLocation) -> Generator[ClueHandle, None, None]:
    handle = ClueHandle(msg, kv, loc)
    token = _clue_stack.set(_clue_stack.get() + (handle,))
    try:
        yield handle
    except BaseException as exc_value:
        snap_msg, snap_kv, snap_loc = handle._snapshot()
        clues: list[ClueRecord] = exc_value.__dict__.setdefault("__clues__", [])
        clues.append(
            ClueRecord(
                msg=snap_msg,
                kv=frozenset((k, deepcopy(v)) for k, v in snap_kv.items()),
                filename=snap_loc.filename,
                lineno=snap_loc.lineno,
            )
        )
        exc_value.add_note(_format_note(snap_msg, snap_kv, snap_loc, len(clues) - 1))
        raise
    finally:
        _clue_stack.reset(token)
