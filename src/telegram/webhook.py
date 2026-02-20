"""FastAPI webhook endpoint for Telegram updates.

Pattern from tg-bot-fastapi-aiogram: feed_webhook_update().
"""

from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, Header, HTTPException, Request

from src.config import get_settings

webhook_router = APIRouter()


@webhook_router.post(get_settings().telegram.webhook_path)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict:
    """Receive Telegram webhook updates."""
    settings = get_settings()

    # Validate secret token if configured
    if settings.telegram.secret_token and settings.telegram.secret_token != "your-secret-token-here":
        if x_telegram_bot_api_secret_token != settings.telegram.secret_token:
            raise HTTPException(status_code=403, detail="Invalid secret token")

    bot: Bot = request.app.state.bot
    dp: Dispatcher = request.app.state.dp

    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_webhook_update(bot, update)

    return {"ok": True}
