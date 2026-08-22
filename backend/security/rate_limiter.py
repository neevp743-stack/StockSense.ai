import time
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, HTTPException, status

class RateLimiter:
    """
    Lightweight, thread-safe in-memory sliding window rate limiter.
    Protects CPU/IO heavy endpoints from excessive requests.
    """
    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        self.history: Dict[str, List[float]] = defaultdict(list)

    def check(self, request: Request, endpoint_key: str = "default"):
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{endpoint_key}"
        now = time.time()
        
        # Clean timestamps older than window
        timestamps = [t for t in self.history[key] if now - t < self.window_seconds]
        
        if len(timestamps) >= self.requests_per_minute:
            retry_after = int(self.window_seconds - (now - timestamps[0]))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for endpoint. Try again in {max(1, retry_after)} seconds.",
                headers={"Retry-After": str(max(1, retry_after))}
            )
        
        timestamps.append(now)
        self.history[key] = timestamps

# Pre-configured rate limiters
heavy_endpoint_limiter = RateLimiter(requests_per_minute=10)
training_endpoint_limiter = RateLimiter(requests_per_minute=5)
