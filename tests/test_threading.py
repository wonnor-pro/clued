import threading
from concurrent.futures import ThreadPoolExecutor

from clued import clue, current_clues


def test_thread_isolation() -> None:
    """Two threads should have independent clue stacks."""
    results: dict[str, tuple[str, ...]] = {}

    def task(name: str) -> None:
        with clue(f"thread {name}"):
            results[name] = tuple(h.msg for h in current_clues())

    t1 = threading.Thread(target=task, args=("A",))
    t2 = threading.Thread(target=task, args=("B",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert results["A"] == ("thread A",)
    assert results["B"] == ("thread B",)


def test_thread_pool() -> None:
    """Thread pool tasks should each see only their own clue."""
    seen: list[tuple[str, ...]] = []

    def worker(n: int) -> None:
        with clue(f"worker {n}"):
            seen.append(tuple(h.msg for h in current_clues()))

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(worker, range(8)))

    for entry in seen:
        assert len(entry) == 1
        assert entry[0].startswith("worker ")
