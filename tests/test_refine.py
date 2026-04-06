import pytest

from clued import clue


def test_refine_updates_kv() -> None:
    with pytest.raises(ValueError) as exc_info:
        with clue("msg") as h:
            h.refine(count=1)
            raise ValueError("x")
    notes = exc_info.value.__notes__
    assert any("count=1" in n for n in notes)


def test_refine_merges() -> None:
    with pytest.raises(ValueError) as exc_info:
        with clue("msg", a=1) as h:
            h.refine(b=2)
            raise ValueError("x")
    notes = exc_info.value.__notes__
    assert any("a=1" in n and "b=2" in n for n in notes)


def test_refine_overwrites() -> None:
    with pytest.raises(ValueError) as exc_info:
        with clue("msg", a=1) as h:
            h.refine(a=99)
            raise ValueError("x")
    notes = exc_info.value.__notes__
    assert any("a=99" in n for n in notes)
    assert not any("a=1" in n for n in notes)


def test_refine_delete_with_none() -> None:
    with pytest.raises(ValueError) as exc_info:
        with clue("msg", a=1) as h:
            h.refine(a=None)
            raise ValueError("x")
    notes = exc_info.value.__notes__
    assert not any("a=" in n for n in notes)


def test_refine_updates_msg() -> None:
    with pytest.raises(ValueError) as exc_info:
        with clue("original") as h:
            h.refine("updated")
            raise ValueError("x")
    notes = exc_info.value.__notes__
    assert any("updated" in n for n in notes)
    assert not any("original" in n for n in notes)


def test_reset() -> None:
    with pytest.raises(ValueError) as exc_info:
        with clue("original", a=1) as h:
            h.refine("changed", b=2)
            h.reset()
            raise ValueError("x")
    notes = exc_info.value.__notes__
    assert any("original" in n for n in notes)
    assert not any("changed" in n for n in notes)
    assert not any("a=" in n or "b=" in n for n in notes)


def test_refine_in_loop() -> None:
    with pytest.raises(ValueError) as exc_info:
        with clue("loop") as h:
            for i in range(5):
                h.refine(iteration=i)
                if i == 3:
                    raise ValueError("at 3")
    notes = exc_info.value.__notes__
    assert any("iteration=3" in n for n in notes)
