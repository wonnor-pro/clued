"""Basic usage examples for clued."""

from clued import clue


def process_order(order_id: str, user_id: int) -> None:
    with clue("processing order", order_id=order_id, user_id=user_id):
        charge_user(order_id, user_id)


def charge_user(order_id: str, user_id: int) -> None:
    with clue("charging user", user_id=user_id) as ctx:
        ctx.refine(step="fetch card")
        card = get_card(user_id)

        ctx.refine(step="apply charge")
        apply_charge(card, order_id)


def get_card(user_id: int) -> str:
    if user_id <= 0:
        raise ValueError("invalid card format")
    return f"card-{user_id}"


def apply_charge(card: str, order_id: str) -> None:
    if not order_id.startswith("ORD-"):
        raise ValueError(f"cannot charge {card!r}: invalid order ID format: {order_id!r}")


if __name__ == "__main__":
    process_order("BAD", -1)
