import time
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, HTTPException, status
from backend.config import settings


class RateLimiter:
    """In-memory sliding window rate limiter per client IP."""
    def __init__(self, max_requests: int = 15, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.hits: Dict[str, List[float]] = defaultdict(list)

    def check(self, ip: str) -> bool:
        now = time.time()
        # Clean older entries
        recent = [t for t in self.hits[ip] if now - t < self.window_seconds]
        if len(recent) >= self.max_requests:
            return False
        recent.append(now)
        self.hits[ip] = recent
        return True


rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_per_minute,
    window_seconds=60
)


async def check_rate_limit(request: Request):
    """FastAPI dependency to enforce rate limit per client IP."""
    client_ip = request.client.host if request.client else "unknown"
    # Check X-Forwarded-For if running behind reverse proxy
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    if not rate_limiter.check(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many investigations. Please wait a minute and try again."
        )
