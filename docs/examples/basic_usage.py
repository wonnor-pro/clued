"""Basic usage examples for clued."""

from clued import clue, get_clues


def process_order(order_id: str, user_id: int) -> None:
    with clue("processing order", order_id=order_id, user_id=user_id) as ctx:
        # Simulate some work
        ctx.refine(step="validate")
        validate_order(order_id)

        ctx.refine(step="charge")
        charge_user(user_id)


def validate_order(order_id: str) -> None:
    if not order_id.startswith("ORD-"):
        raise ValueError(f"Invalid order ID format: {order_id!r}")


def charge_user(user_id: int) -> None:
    if user_id <= 0:
        raise RuntimeError("Cannot charge invalid user")


if __name__ == "__main__":
    try:
        process_order("BAD", -1)
    except Exception as e:
        print("Exception:", e)
        print()
        print("Notes added to exception:")
        for note in getattr(e, "__notes__", []):
            print("\t", note)
        print()
        print("Structured clues:")
        for c in get_clues(e):
            print("\t", f"{c.msg} {c.kv} at {c.filename}:{c.lineno}")
        print()

        raise
