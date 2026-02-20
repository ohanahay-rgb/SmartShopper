"""Format product search results as clean Hebrew Telegram messages."""

from __future__ import annotations

SEPARATOR = "\u2500" * 25


def format_result(rank: int, product: dict) -> str:
    """Format a single product result -- clean, no emojis."""
    return (
        f"<b>{rank}. {product['name']}</b> | {product['source']}\n"
        f"   \u20aa{product['price']:.0f}"
        f"   \u05de\u05e9\u05dc\u05d5\u05d7: \u20aa{product['shipping_cost']}"
        f'   \u05e1\u05d4"\u05db: <b>\u20aa{product["total_cost"]:.0f}</b>'
    )


def format_results(query: str, products: list[dict]) -> str:
    """Format all 5 product results into a single clean message."""
    header = f'<b>{query}</b>\n{SEPARATOR}'

    items = "\n\n".join(
        format_result(i + 1, p) for i, p in enumerate(products)
    )

    cheapest = min(p["total_cost"] for p in products) if products else 0
    summary = (
        f"\n{SEPARATOR}\n"
        f"{len(products)} "
        f'| \u20aa{cheapest:.0f} \u05e1\u05d4"\u05db'
    )

    return f"{header}\n\n{items}{summary}"
