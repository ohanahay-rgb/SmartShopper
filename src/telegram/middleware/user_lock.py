"""Per-user lock middleware -- one search at a time per user.

Prevents users from flooding the system with concurrent searches.
Uses in-memory asyncio.Lock per user_id.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message


class UserLockMiddleware(BaseMiddleware):
    """Outer middleware: skip handler if user already has a search running."""

    def __init__(self) -> None:
        self._locks: dict[int, asyncio.Lock] = {}

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id if event.from_user else 0

        # Commands always pass through (e.g. /start)
        if event.text and event.text.startswith("/"):
            return await handler(event, data)

        # Get or create lock for this user
        if user_id not in self._locks:
            self._locks[user_id] = asyncio.Lock()

        lock = self._locks[user_id]

        if lock.locked():
            await event.answer("חיפוש קודם עדיין בתהליך, נא להמתין...")
            return None

        async with lock:
            return await handler(event, data)
