import pytest

from clued import clue, current_clues, get_clue_dict, get_clues


def test_get_clues_empty() -> None:
    exc = ValueError("no clues")
    assert get_clues(exc) == []


def test_get_clues_ordered() -> None:
    with pytest.raises(ValueError) as exc_info:
        with clue("outer", a=1):
            with clue("inner", b=2):
                raise ValueError("x")
    clues = get_clues(exc_info.value)
    assert len(clues) == 2
    # inner is appended first (innermost exception handler fires first)
    assert clues[0].msg == "inner"
    assert clues[1].msg == "outer"


def test_get_clue_dict_merge() -> None:
    with pytest.raises(ValueError) as exc_info:
        with clue("outer", a=1, shared=0):
            with clue("inner", b=2, shared=99):
                raise ValueError("x")
    d = get_clue_dict(exc_info.value)
    assert d["a"] == 1
    assert d["b"] == 2
    assert d["shared"] == 99  # inner overrides outer


def test_get_clue_dict_empty() -> None:
    exc = ValueError("no clues")
    assert get_clue_dict(exc) == {}


def test_current_clues_inside_context() -> None:
    with clue("active") as h:
        stack = current_clues()
        assert h in stack


def test_current_clues_outside_context() -> None:
    stack = current_clues()
    assert stack == ()
