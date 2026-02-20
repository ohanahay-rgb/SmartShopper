"""Format product search results as Hebrew Telegram messages."""

from __future__ import annotations


def format_result(rank: int, product: dict) -> str:
    """Format a single product result."""
    return (
        f"<b>{rank}. {product['name']}</b>\n"
        f"   {product['source']} | {product['distance_km']} ק\"מ | {product['delivery_days']}\n"
        f"   מחיר: {product['price']:.2f} \u20aa"
        f" | שיליחויות: {product['shipping_cost']} \u20aa"
        f" | סה\"כ: {product['total_cost']:.2f} \u20aa"
    )


def format_results(query: str, products: list[dict]) -> str:
    """Format all 5 product results into a single message."""
    header = f"תוצאות עבור \"<b>{query}</b>\":\n"
    items = "\n\n".join(
        format_result(i + 1, p) for i, p in enumerate(products)
    )
    return f"{header}\n{items}"
