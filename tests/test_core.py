import pytest

from clued import ClueRecord, clue


def test_basic_context() -> None:
    with pytest.raises(ValueError) as exc_info:
        with clue("processing failed"):
            raise ValueError("boom")
    notes = exc_info.value.__notes__
    assert any("0: processing failed" in n for n in notes)


def test_preserves_exception_type() -> None:
    with pytest.raises(ValueError):
        with clue("msg"):
            raise ValueError("still a ValueError")


def test_nested_contexts() -> None:
    with pytest.raises(RuntimeError) as exc_info:
        with clue("outer"):
            with clue("inner"):
                raise RuntimeError("nested")
    notes = exc_info.value.__notes__
    assert len(notes) == 2
    assert "inner" in notes[0]
    assert "outer" in notes[1]


def test_kv_pairs() -> None:
    with pytest.raises(ValueError) as exc_info:
        with clue("msg", user_id=5):
            raise ValueError("x")
    notes = exc_info.value.__notes__
    assert any("user_id=5" in n for n in notes)


def test_no_exception_no_side_effects() -> None:
    with clue("msg") as h:
        pass
    assert not hasattr(h, "__notes__")


def test_base_exception() -> None:
    with pytest.raises(KeyboardInterrupt) as exc_info:
        with clue("interrupted"):
            raise KeyboardInterrupt()
    notes = exc_info.value.__notes__
    assert any("interrupted" in n for n in notes)


def test_source_location() -> None:
    with pytest.raises(ValueError) as exc_info:
        with clue("loc test"):  # this line's number is captured
            raise ValueError("x")
    notes = exc_info.value.__notes__
    assert any("test_core.py" in n for n in notes)


def test_clues_attribute() -> None:
    with pytest.raises(ValueError) as exc_info:
        with clue("structured", order_id="abc"):
            raise ValueError("x")
    clues: list[ClueRecord] = exc_info.value.__clues__  # type: ignore[attr-defined]
    assert len(clues) == 1
    c = clues[0]
    assert c.msg == "structured"
    assert c.kv == frozenset((("order_id", "abc"),))
    assert "test_core.py" in c.loc.filename
    assert isinstance(c.loc.lineno, int)
