import logging
import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware.
    Limits requests per IP address to prevent API abuse.
    
    Note: For production, use Redis-backed rate limiting for distributed systems.
    """

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = defaultdict(list)
        self.cleanup_interval = 60  # Clean up old entries every 60 seconds
        self.last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        
        if request.url.path == "/health":
            return await call_next(request)
        
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_entries(current_time)
            self.last_cleanup = current_time
        
        timestamps = self.request_counts[client_ip]
        
        cutoff_time = current_time - 60
        timestamps[:] = [ts for ts in timestamps if ts > cutoff_time]
        
        if len(timestamps) >= self.requests_per_minute:
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "client_ip": client_ip,
                    "path": request.url.path,
                    "requests_in_window": len(timestamps),
                    "limit": self.requests_per_minute,
                },
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": 60,
                },
                headers={"Retry-After": "60"},
            )
        
        timestamps.append(current_time)
        
        response = await call_next(request)
        
        remaining = self.requests_per_minute - len(timestamps)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))
        
        return response

    def _cleanup_old_entries(self, current_time: float):
        """Remove entries for IPs that haven't made requests recently."""
        cutoff_time = current_time - 300  # 5 minutes
        ips_to_remove = []
        
        for ip, timestamps in self.request_counts.items():
            if not timestamps or max(timestamps) < cutoff_time:
                ips_to_remove.append(ip)
        
        for ip in ips_to_remove:
            del self.request_counts[ip]
        
        if ips_to_remove:
            logger.debug(f"Cleaned up rate limit data for {len(ips_to_remove)} IPs")

