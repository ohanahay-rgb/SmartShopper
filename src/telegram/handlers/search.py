"""Product search handler -- receives text, returns 5 stub results.

In the future this will invoke the agent pipeline. For now, returns
hardcoded stub data to verify the full Telegram flow works.
"""

from __future__ import annotations

from aiogram import Router
from aiogram.types import Message

from src.telegram.formatters import format_results
from src.telegram.keyboards import build_result_keyboard

router = Router(name="search")

# Stub products for Phase 2 testing
STUB_PRODUCTS: list[dict] = [
    {
        "id": 1,
        "name": "Sony WH-1000XM4",
        "source": "KSP",
        "price": 279.90,
        "shipping_cost": 128,
        "total_cost": 407.90,
        "distance_km": 12,
        "delivery_days": "1-2 ימים",
        "url": "https://ksp.co.il/item/12345",
    },
    {
        "id": 2,
        "name": "JBL Tune 520BT",
        "source": "Bug",
        "price": 149.00,
        "shipping_cost": 86,
        "total_cost": 235.00,
        "distance_km": 8,
        "delivery_days": "1-2 ימים",
        "url": "https://bug.co.il/item/67890",
    },
    {
        "id": 3,
        "name": "Samsung Galaxy Buds2 Pro",
        "source": "Ivory",
        "price": 349.00,
        "shipping_cost": 155,
        "total_cost": 504.00,
        "distance_km": 25,
        "delivery_days": "2-3 ימים",
        "url": "https://ivory.co.il/item/11111",
    },
    {
        "id": 4,
        "name": "Apple AirPods 3",
        "source": "iDigital",
        "price": 499.00,
        "shipping_cost": 95,
        "total_cost": 594.00,
        "distance_km": 5,
        "delivery_days": "1 יום",
        "url": "https://idigital.co.il/item/22222",
    },
    {
        "id": 5,
        "name": "Xiaomi Redmi Buds 4",
        "source": "Zap",
        "price": 89.90,
        "shipping_cost": 110,
        "total_cost": 199.90,
        "distance_km": 15,
        "delivery_days": "2-3 ימים",
        "url": "https://zap.co.il/item/33333",
    },
]


@router.message()
async def handle_search(message: Message) -> None:
    """Handle free-text product search."""
    query = message.text
    if not query or query.startswith("/"):
        return

    # Send "searching" indicator
    status_msg = await message.answer("מחפש...")

    # Sort stub results by total_cost (cheapest first)
    sorted_products = sorted(STUB_PRODUCTS, key=lambda p: p["total_cost"])

    # Send formatted results header
    text = format_results(query, sorted_products)
    await status_msg.edit_text(text)

    # Send each result with its keyboard
    for product in sorted_products:
        keyboard = build_result_keyboard(product["id"], product["url"])
        await message.answer(
            f"<b>{product['name']}</b> - {product['total_cost']:.2f} \u20aa",
            reply_markup=keyboard,
        )
