"""InlineKeyboard builders for product results.

Business rule: each result has exactly 2 buttons:
  [קנייה ישירה] (URL) + [הזמן שיליחויות] (callback)
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def build_result_keyboard(product_id: int, product_url: str) -> InlineKeyboardMarkup:
    """Build 2-button keyboard for a single product result."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="קנייה ישירה",
                    url=product_url,
                ),
                InlineKeyboardButton(
                    text="הזמן שיליחויות",
                    callback_data=f"deliver_{product_id}",
                ),
            ]
        ]
    )
