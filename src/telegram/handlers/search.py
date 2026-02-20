"""Product search handler -- routes through Shufi AI agent.

All text messages go to Shufi's state machine. Shufi guides the
conversation (asking brand/budget/location) and signals when to search.
"""

from __future__ import annotations

from aiogram import Router
from aiogram.types import Message

from src.agents.sales_agent import shufi
from src.monitoring.discord_logger import log_search_completed, log_search_started
from src.telegram.formatters import format_results
from src.telegram.keyboards import build_result_keyboard

router = Router(name="search")

# Stub products for testing (8 results, sorted cheapest first)
STUB_PRODUCTS: list[dict] = [
    {
        "id": 1,
        "name": "Xiaomi Redmi Buds 4",
        "source": "Zap",
        "price": 89.90,
        "shipping_cost": 110,
        "total_cost": 200,
        "distance_km": 15,
        "delivery_days": "2-3 ימים",
        "url": "https://zap.co.il/item/33333",
    },
    {
        "id": 2,
        "name": "JBL Tune 520BT",
        "source": "Bug",
        "price": 149.00,
        "shipping_cost": 86,
        "total_cost": 235,
        "distance_km": 8,
        "delivery_days": "1-2 ימים",
        "url": "https://bug.co.il/item/67890",
    },
    {
        "id": 3,
        "name": "Sony WH-1000XM4",
        "source": "KSP",
        "price": 279.90,
        "shipping_cost": 128,
        "total_cost": 408,
        "distance_km": 12,
        "delivery_days": "1-2 ימים",
        "url": "https://ksp.co.il/item/12345",
    },
    {
        "id": 4,
        "name": "Samsung Galaxy Buds2 Pro",
        "source": "Ivory",
        "price": 349.00,
        "shipping_cost": 155,
        "total_cost": 504,
        "distance_km": 25,
        "delivery_days": "2-3 ימים",
        "url": "https://ivory.co.il/item/11111",
    },
    {
        "id": 5,
        "name": "Beats Studio Buds+",
        "source": "iDigital",
        "price": 399.00,
        "shipping_cost": 95,
        "total_cost": 494,
        "distance_km": 5,
        "delivery_days": "1 יום",
        "url": "https://idigital.co.il/item/44444",
    },
    {
        "id": 6,
        "name": "Apple AirPods 3",
        "source": "Machsanei Hashmal",
        "price": 499.00,
        "shipping_cost": 110,
        "total_cost": 609,
        "distance_km": 18,
        "delivery_days": "1-2 ימים",
        "url": "https://machsanei.co.il/item/55555",
    },
    {
        "id": 7,
        "name": "Bose QuietComfort 45",
        "source": "Amazon IL",
        "price": 599.00,
        "shipping_cost": 140,
        "total_cost": 739,
        "distance_km": 30,
        "delivery_days": "3-5 ימים",
        "url": "https://amazon.co.il/item/66666",
    },
    {
        "id": 8,
        "name": "Sony WH-1000XM5",
        "source": "Lastprice",
        "price": 849.00,
        "shipping_cost": 95,
        "total_cost": 944,
        "distance_km": 7,
        "delivery_days": "1-2 ימים",
        "url": "https://lastprice.co.il/item/77777",
    },
]


@router.message()
async def handle_message(message: Message) -> None:
    """Route all text through Shufi, show results when Shufi says to search."""
    query = message.text
    if not query or query.startswith("/"):
        return

    user_id = message.from_user.id if message.from_user else 0

    # Shufi handles the conversation and decides when to search
    shufi_response, should_search = await shufi.handle_message(user_id, query)

    # Always show Shufi's response
    await message.answer(f"<b>שופי:</b> {shufi_response}")

    # Show search results only when Shufi signals ready
    if should_search:
        start_time = await log_search_started(query, user_id)

        sorted_products = sorted(STUB_PRODUCTS, key=lambda p: p["total_cost"])

        text = format_results(query, sorted_products)
        await message.answer(text)

        for product in sorted_products:
            keyboard = build_result_keyboard(product["id"], product["url"])
            await message.answer(
                f"<b>{product['name']}</b> | \u20aa{product['total_cost']:.0f}",
                reply_markup=keyboard,
            )

        await log_search_completed(query, len(sorted_products), start_time)
