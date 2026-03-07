"""Lightweight in-memory rate limiter (per IP, no external deps)."""

import time
from fastapi import Request, HTTPException

# IP → last request timestamp
_timestamps: dict[str, float] = {}

MIN_INTERVAL_SECONDS = 2.0


async def check_rate_limit(request: Request) -> None:
    """Raise HTTP 429 if the same IP calls within MIN_INTERVAL_SECONDS."""
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    last = _timestamps.get(ip)

    if last is not None and (now - last) < MIN_INTERVAL_SECONDS:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait a moment and try again.",
        )

    _timestamps[ip] = now
