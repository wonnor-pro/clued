import functools
import inspect
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

from typing_extensions import ParamSpec

from clued._core import clue

T = TypeVar("T")
P = ParamSpec("P")


def clue_on_error(msg_template: str, **extra_kv: Any) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator that attaches a formatted clue context on error."""

    def decorator(fn: Callable[P, T]) -> Callable[P, T]:
        sig = inspect.signature(fn)

        @functools.wraps(fn)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            formatted = msg_template.format(**bound.arguments)
            with clue(formatted, **extra_kv):
                return fn(*args, **kwargs)

        return sync_wrapper

    return decorator


def clue_on_error_async(
    msg_template: str, **extra_kv: Any
) -> Callable[[Callable[P, Coroutine[Any, Any, T]]], Callable[P, Coroutine[Any, Any, T]]]:
    def decorator(fn: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, Coroutine[Any, Any, T]]:
        sig = inspect.signature(fn)

        @functools.wraps(fn)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            formatted = msg_template.format(**bound.arguments)
            with clue(formatted, **extra_kv):
                return await fn(*args, **kwargs)

        return async_wrapper

    return decorator
