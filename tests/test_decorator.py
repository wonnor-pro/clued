import pytest

from clued import clue_on_error


def test_basic_decorator() -> None:
    @clue_on_error("processing user")
    def process(user_id: int) -> None:
        raise ValueError("fail")

    with pytest.raises(ValueError) as exc_info:
        process(42)
    notes = exc_info.value.__notes__
    assert any("processing user" in n for n in notes)


def test_template_formatting() -> None:
    @clue_on_error("loading {name}")
    def load(name: str) -> None:
        raise RuntimeError("not found")

    with pytest.raises(RuntimeError) as exc_info:
        load("config.json")
    notes = exc_info.value.__notes__
    assert any("loading config.json" in n for n in notes)


def test_preserves_function_metadata() -> None:
    @clue_on_error("msg")
    def my_func() -> None:
        """My docstring."""

    assert my_func.__name__ == "my_func"
    assert my_func.__doc__ == "My docstring."


def test_no_error_no_overhead() -> None:
    @clue_on_error("msg")
    def happy() -> int:
        return 42

    assert happy() == 42


@pytest.mark.asyncio
async def test_async_decorator() -> None:
    @clue_on_error("async op {x}")
    async def async_op(x: int) -> None:
        raise ValueError("async fail")

    with pytest.raises(ValueError) as exc_info:
        await async_op(7)
    notes = exc_info.value.__notes__
    assert any("async op 7" in n for n in notes)
