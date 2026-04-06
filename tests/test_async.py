import asyncio

import pytest

from clued import clue, clue_on_error, current_clues


@pytest.mark.asyncio
async def test_async_basic() -> None:
    with pytest.raises(ValueError) as exc_info:
        async with _async_clue("async basic"):
            raise ValueError("x")
    notes = exc_info.value.__notes__
    assert any("async basic" in n for n in notes)


@pytest.mark.asyncio
async def test_async_gather_isolation() -> None:
    """Each gathered task should have its own clue stack."""
    results: list[tuple[str, ...]] = []

    async def task(name: str) -> None:
        with clue(f"task {name}"):
            await asyncio.sleep(0)
            stack = current_clues()
            results.append(tuple(h.msg for h in stack))

    await asyncio.gather(task("A"), task("B"))
    assert ("task A",) in results
    assert ("task B",) in results


@pytest.mark.asyncio
async def test_async_nested_tasks() -> None:
    with pytest.raises(ValueError) as exc_info:
        with clue("outer"):
            async with _async_clue("inner"):
                raise ValueError("nested async")
    notes = exc_info.value.__notes__
    assert len(notes) == 2


@pytest.mark.asyncio
async def test_async_sequential_refine() -> None:
    with pytest.raises(ValueError) as exc_info:
        async with _async_clue("sequential") as h:
            h.refine(step=1)
            await asyncio.sleep(0)
            h.refine(step=2)
            raise ValueError("at step 2")
    notes = exc_info.value.__notes__
    assert any("step=2" in n for n in notes)


@pytest.mark.asyncio
async def test_async_decorator() -> None:
    @clue_on_error("decorated async {val}")
    async def op(val: int) -> None:
        raise ValueError("fail")

    with pytest.raises(ValueError) as exc_info:
        await op(5)
    notes = exc_info.value.__notes__
    assert any("decorated async 5" in n for n in notes)


class _async_clue:
    """Thin async context manager wrapping clue() for test use."""

    def __init__(self, msg: str, **kv: object) -> None:
        self._cm = clue(msg, **kv)

    async def __aenter__(self) -> object:
        return self._cm.__enter__()

    async def __aexit__(self, *args: object) -> object:
        return self._cm.__exit__(*args)
