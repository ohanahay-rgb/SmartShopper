"""/start command handler -- Hebrew welcome message."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router(name="start")

WELCOME_TEXT = (
    "<b>SmartShopper</b>\n"
    "\u2500" * 25 + "\n\n"
    "היי! אני שופי, העוזר החכם שלך להשוואת מחירים.\n\n"
    "סורק 15+ חנויות ומחזיר לך 5 המחירים הכי טובים, "
    'כולל עלות משלוח עם שיליחויות בע"מ.\n\n'
    "כתוב שם מוצר ואני אטפל בשאר!\n"
    "לדוגמה: <i>אוזניות בלוטוס</i>"
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Send Hebrew welcome message with usage instructions."""
    await message.answer(WELCOME_TEXT)
