"""Lightweight in-memory rate limiter (per IP + endpoint, no external deps).

Uses a sliding-window counter so that sequential calls in a comparison
flow (upload A, analyze A, upload B, analyze B, compare) are not blocked.
"""

import time
from collections import defaultdict
from fastapi import Request, HTTPException

# (IP, path) → list of request timestamps (sliding window)
_request_log: dict[str, list[float]] = defaultdict(list)

# Max requests per window per IP
MAX_REQUESTS = 30
WINDOW_SECONDS = 60.0


def _clean_old(entries: list[float], now: float) -> list[float]:
    """Remove entries older than the window."""
    cutoff = now - WINDOW_SECONDS
    return [t for t in entries if t > cutoff]


async def check_rate_limit(request: Request) -> None:
    """Raise HTTP 429 if the same IP exceeds MAX_REQUESTS in WINDOW_SECONDS."""
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()

    entries = _clean_old(_request_log[ip], now)

    if len(entries) >= MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait a moment and try again.",
        )

    entries.append(now)
    _request_log[ip] = entries
