"""SmartShopper FastAPI application with Telegram bot integration.

Supports two modes:
- Webhook mode (production): set TELEGRAM_WEBHOOK_URL in .env
- Polling mode (local dev): leave TELEGRAM_WEBHOOK_URL empty or as placeholder
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from src.config import get_settings
from src.telegram.bot import create_bot, create_dispatcher
from src.telegram.webhook import webhook_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown lifecycle for bot and webhook."""
    settings = get_settings()
    bot = create_bot()
    dp = create_dispatcher()

    # Store on app state for webhook access
    app.state.bot = bot
    app.state.dp = dp

    webhook_url = settings.telegram.webhook_url
    use_webhook = webhook_url and not webhook_url.startswith("https://your-")

    polling_task = None

    if use_webhook:
        # Production: set webhook
        full_url = f"{webhook_url}{settings.telegram.webhook_path}"
        await bot.set_webhook(
            url=full_url,
            secret_token=settings.telegram.secret_token or None,
        )
        logger.info("Telegram webhook set: %s", full_url)
    else:
        # Local dev: delete any old webhook, then start polling
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Polling mode -- starting Telegram bot polling")
        polling_task = asyncio.create_task(_run_polling(dp, bot))

    yield

    if use_webhook:
        await bot.delete_webhook()
        logger.info("Telegram webhook deleted")
    elif polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass

    await bot.session.close()


async def _run_polling(dp, bot) -> None:
    """Run dispatcher polling (for local development)."""
    try:
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="SmartShopper",
    description="AI-powered product comparison for Israel",
    lifespan=lifespan,
)

app.include_router(webhook_router)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}
