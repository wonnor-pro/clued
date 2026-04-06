import time

from clued import clue


def test_happy_path_overhead() -> None:
    """100k with clue(): pass should complete in under 1 second."""
    start = time.perf_counter()
    for _ in range(100_000):
        with clue("noop"):
            pass
    elapsed = time.perf_counter() - start
    assert elapsed < 1.0, f"happy path took {elapsed:.3f}s"


def test_refine_overhead() -> None:
    """100k refine() calls should complete in under 0.5 seconds."""
    start = time.perf_counter()
    with clue("base") as h:
        for i in range(100_000):
            h.refine(i=i)
    elapsed = time.perf_counter() - start
    assert elapsed < 0.5, f"refine overhead took {elapsed:.3f}s"


def test_error_path() -> None:
    """10k exceptions with 3 nested clues should complete in reasonable time."""
    start = time.perf_counter()
    for _ in range(10_000):
        try:
            with clue("outer"):
                with clue("middle"):
                    with clue("inner"):
                        raise ValueError("perf")
        except ValueError:
            pass
    elapsed = time.perf_counter() - start
    assert elapsed < 5.0, f"error path took {elapsed:.3f}s"
