"""Discord webhook logger for SmartShopper events.

Sends colored embed messages to Discord for:
- Search started (blue)
- Search completed (green)
- Site blocked (yellow)
- Critical error (red)
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import httpx

from src.config import get_settings

logger = logging.getLogger(__name__)

# Discord embed colors
COLOR_BLUE = 0x3498DB    # search started
COLOR_GREEN = 0x2ECC71   # search completed
COLOR_YELLOW = 0xF1C40F  # site blocked
COLOR_RED = 0xE74C3C     # critical error


def _now_israel() -> str:
    """Current time formatted for Israel timezone."""
    from zoneinfo import ZoneInfo
    now = datetime.now(ZoneInfo("Asia/Jerusalem"))
    return now.strftime("%H:%M:%S %d/%m/%Y")


async def _send_embed(title: str, description: str, color: int, fields: list[dict] | None = None) -> None:
    """Send a Discord embed message via webhook."""
    settings = get_settings()
    url = settings.discord_webhook_url
    if not url or "your-webhook-url" in url:
        return

    embed: dict = {
        "title": title,
        "description": description,
        "color": color,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": f"SmartShopper | {_now_israel()}"},
    }
    if fields:
        embed["fields"] = fields

    payload = {"embeds": [embed]}

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=5.0)
            if resp.status_code not in (200, 204):
                logger.warning("Discord webhook returned %s", resp.status_code)
    except Exception:
        logger.exception("Failed to send Discord webhook")


async def log_search_started(product: str, user_id: int) -> float:
    """Log that a search has started. Returns start time for duration calc."""
    await _send_embed(
        title="חיפוש חדש התחיל",
        description=f"**{product}**",
        color=COLOR_BLUE,
        fields=[
            {"name": "לקוח", "value": str(user_id), "inline": True},
        ],
    )
    return time.monotonic()


async def log_search_completed(product: str, result_count: int, start_time: float) -> None:
    """Log that a search completed successfully."""
    duration = time.monotonic() - start_time
    await _send_embed(
        title="חיפוש הושלם",
        description=f"**{product}**",
        color=COLOR_GREEN,
        fields=[
            {"name": "תוצאות", "value": str(result_count), "inline": True},
            {"name": "זמן", "value": f"{duration:.1f}s", "inline": True},
        ],
    )


async def log_site_blocked(site: str, status_code: int) -> None:
    """Log that a scraping site returned 403/429."""
    await _send_embed(
        title="אתר חסום",
        description=f"**{site}** החזיר {status_code}",
        color=COLOR_YELLOW,
        fields=[
            {"name": "קוד", "value": str(status_code), "inline": True},
        ],
    )


async def log_critical_error(error: str, details: str = "") -> None:
    """Log a critical error."""
    await _send_embed(
        title="שגיאה קריטית",
        description=f"```{error}```",
        color=COLOR_RED,
        fields=[
            {"name": "פרטים", "value": details or "N/A", "inline": False},
        ] if details else None,
    )
