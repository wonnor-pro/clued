import inspect
from typing import Any

from clued._core import clue


def ctx(fn: Any, *args: Any, msg: str, **kv: Any) -> Any:
    """Inline wrapper: call fn(*args) inside a clue context."""
    if inspect.iscoroutinefunction(fn):
        return _async_ctx(fn, *args, msg=msg, **kv)
    with clue(msg, **kv):
        return fn(*args)


async def _async_ctx(fn: Any, *args: Any, msg: str, **kv: Any) -> Any:
    with clue(msg, **kv):
        return await fn(*args)
