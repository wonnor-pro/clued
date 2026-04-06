import asyncio

import pytest

from clued import clue, clue_on_error_async, current_clues


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
async def test_async_decorator() -> None:
    @clue_on_error_async("decorated async {val}")
    async def op(val: int) -> None:
        raise ValueError("fail")

    with pytest.raises(ValueError) as exc_info:
        await op(5)
    notes = exc_info.value.__notes__
    assert any("decorated async 5" in n for n in notes)
