"""Batch processing example showing refine() in a loop."""

from collections.abc import Mapping, Sequence

from clued import clue


def process_batch(items: Sequence[dict[str, str | bool]]) -> list[dict[str, str | bool]]:
    results = []
    with clue("batch processing", total=len(items)) as ctx:
        for i, item in enumerate(items):
            ctx.refine(index=i, item_id=item.get("id"))
            result = process_item(item)
            results.append(result)
    return results


def process_item(item: Mapping[str, str | bool]) -> dict[str, str | bool]:
    if item.get("invalid"):
        raise ValueError(f"Item {item['id']} is invalid")
    return {"id": item["id"], "processed": True}


if __name__ == "__main__":
    batch: list[dict[str, str | bool]] = [
        {"id": "a"},
        {"id": "b"},
        {"id": "c", "invalid": True},
        {"id": "d"},
    ]
    process_batch(batch)
