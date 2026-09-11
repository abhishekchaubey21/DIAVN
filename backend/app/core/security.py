import time
import logging
from collections import defaultdict
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """
    Lightweight, zero-dependency sliding window rate limiter.
    Stores timestamp history per IP address in memory without introducing Redis.
    """
    def __init__(self, requests_per_minute: int = 60, burst_limit: int = 15):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self._window_sec = 60
        self._ip_records: Dict[str, list] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> Tuple[bool, Optional[int]]:
        """
        Evaluates whether request from client_ip is permitted.
        Returns: (is_allowed: bool, retry_after_sec: Optional[int])
        """
        now = time.time()
        window_start = now - self._window_sec
        timestamps = self._ip_records[client_ip]

        # Purge stale timestamps older than 60 seconds
        self._ip_records[client_ip] = [ts for ts in timestamps if ts > window_start]
        active_count = len(self._ip_records[client_ip])

        if active_count >= self.requests_per_minute:
            oldest_in_window = self._ip_records[client_ip][0]
            retry_after = max(1, int(oldest_in_window + self._window_sec - now))
            return False, retry_after

        self._ip_records[client_ip].append(now)
        return True, None

    def reset(self):
        """Clears rate limit records (used in test fixtures)."""
        self._ip_records.clear()


rate_limiter = InMemoryRateLimiter(requests_per_minute=60, burst_limit=20)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware applying rate limits to sensitive mutation and upload routes.
    """
    SENSITIVE_PREFIXES = ("/api/v1/invoices", "/api/v1/images", "/api/v1/workflow/events", "/invoices", "/images")

    async def dispatch(self, request: Request, call_next):
        # Exclude read-only GET requests or health probes from rate limits
        if request.method in ["POST", "PUT", "DELETE"]:
            path = request.url.path
            if any(path.startswith(prefix) for prefix in self.SENSITIVE_PREFIXES):
                client_ip = request.client.host if request.client else "127.0.0.1"
                allowed, retry_after = rate_limiter.is_allowed(client_ip)
                if not allowed:
                    logger.warning(f"Rate limit exceeded for IP: {client_ip} on path: {path}")
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": "Too Many Requests",
                            "message": f"Rate limit exceeded. Please retry after {retry_after} seconds.",
                            "retry_after_seconds": retry_after
                        },
                        headers={"Retry-After": str(retry_after)}
                    )

        response = await call_next(request)
        return response
