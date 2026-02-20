"""Rate limiting middleware -- token bucket per user.

Allows max 15 requests per 60 seconds per user.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message

MAX_REQUESTS = 15
WINDOW_SECONDS = 60.0


class RateLimitMiddleware(BaseMiddleware):
    """Outer middleware: reject messages if user exceeds rate limit."""

    def __init__(self) -> None:
        # {user_id: list of timestamps}
        self._requests: dict[int, list[float]] = {}

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id if event.from_user else 0

        # Commands always pass through
        if event.text and event.text.startswith("/"):
            return await handler(event, data)

        now = time.monotonic()

        # Clean old entries
        if user_id in self._requests:
            self._requests[user_id] = [
                t for t in self._requests[user_id]
                if now - t < WINDOW_SECONDS
            ]
        else:
            self._requests[user_id] = []

        if len(self._requests[user_id]) >= MAX_REQUESTS:
            await event.answer(
                f"נא להמתין - ניתן לבצע עד {MAX_REQUESTS} חיפושים בדקה."
            )
            return None

        self._requests[user_id].append(now)
        return await handler(event, data)
