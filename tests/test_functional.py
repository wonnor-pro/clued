import pytest

from clued import ctx


def test_ctx_success() -> None:
    result = ctx(lambda: 42, msg="computing")
    assert result == 42


def test_ctx_error() -> None:
    def fail() -> None:
        raise ValueError("ctx fail")

    with pytest.raises(ValueError) as exc_info:
        ctx(fail, msg="calling fail")
    notes = exc_info.value.__notes__
    assert any("calling fail" in n for n in notes)


@pytest.mark.asyncio
async def test_ctx_async() -> None:
    async def async_fail() -> None:
        raise RuntimeError("async ctx fail")

    with pytest.raises(RuntimeError) as exc_info:
        await ctx(async_fail, msg="async op")
    notes = exc_info.value.__notes__
    assert any("async op" in n for n in notes)
