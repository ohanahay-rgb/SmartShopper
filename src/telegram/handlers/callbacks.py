"""Callback query handlers for inline keyboard buttons."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

router = Router(name="callbacks")


@router.callback_query(F.data.startswith("deliver_"))
async def handle_deliver(callback: CallbackQuery) -> None:
    """Handle 'Order Shilichuyot' button press."""
    product_id = callback.data.split("_", 1)[1] if callback.data else "?"
    await callback.answer()
    await callback.message.answer(
        f"מזמין שיליחויות למוצר #{product_id}...\n"
        "בקרוב תקבל אישור הזמנה."
    )
