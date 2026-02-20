"""Aiogram Bot + Dispatcher factory.

Pattern from tg-bot-fastapi-aiogram: create Bot and Dispatcher,
register all routers and middleware.
"""

from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.config import get_settings
from src.telegram.handlers import callbacks, search, start
from src.telegram.middleware.rate_limit import RateLimitMiddleware
from src.telegram.middleware.user_lock import UserLockMiddleware


def create_dispatcher() -> Dispatcher:
    """Create Dispatcher with all routers and middleware registered."""
    dp = Dispatcher()

    # Middleware (outer -- runs before routers)
    dp.message.outer_middleware(UserLockMiddleware())
    dp.message.outer_middleware(RateLimitMiddleware())

    # Routers (order matters: commands first, then text, then callbacks)
    dp.include_router(start.router)
    dp.include_router(search.router)
    dp.include_router(callbacks.router)

    return dp


def create_bot() -> Bot:
    """Create Bot instance with token from settings."""
    settings = get_settings()
    return Bot(
        token=settings.telegram.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
