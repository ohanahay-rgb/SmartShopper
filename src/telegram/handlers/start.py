"""/start command handler -- Hebrew welcome message."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Send Hebrew welcome message with usage instructions."""
    await message.answer(
        "<b>SmartShopper</b> - השוואת מחירים חכמה\n\n"
        "שלח לי שם מוצר ואמצא לך את 5 המחירים הטובים ביותר "
        "מ-15+ חנויות ישראליות, כולל עלות משלוח עם שיליחויות בע\"מ.\n\n"
        "לדוגמה: <i>אוזניות בלוטוס</i>\n\n"
        "פשוט כתוב מה אתה מחפש ואני אטפל בשאר."
    )
