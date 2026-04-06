import functools
import inspect
from collections.abc import Callable
from typing import Any

from clued._core import clue


def clue_on_error(msg_template: str, **extra_kv: Any) -> Callable[[Any], Any]:
    """Decorator that attaches a formatted clue context on error."""

    def decorator(fn: Any) -> Any:
        sig = inspect.signature(fn)

        if inspect.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                formatted = msg_template.format(**bound.arguments)
                with clue(formatted, **extra_kv):
                    return await fn(*args, **kwargs)

            return async_wrapper

        else:

            @functools.wraps(fn)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                formatted = msg_template.format(**bound.arguments)
                with clue(formatted, **extra_kv):
                    return fn(*args, **kwargs)

            return sync_wrapper

    return decorator
