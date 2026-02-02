"""
ELK Server - Rate Limiter
Zero-dependency implementation of Token Bucket algorithm for API rate limiting.

Features:
- IP-based limiting
- Token bucket algorithm
- Clean scaffolding for future Redis integration
"""

import time
import threading
from typing import Dict, Tuple
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class RateLimiter:
    """
    Token Bucket Rate Limiter.
    Rate: tokens per second
    Capacity: max burst size
    """
    
    def __init__(self, rate: float = 2.0, capacity: int = 10):
        self.rate = rate
        self.capacity = capacity
        # Mapping IP -> (tokens, last_update)
        self.buckets: Dict[str, Tuple[float, float]] = {}
        self.lock = threading.Lock()
    
    def check_limit(self, ip: str) -> bool:
        """
        Check if request is allowed.
        Returns True if allowed, False if limited.
        """
        now = time.time()
        
        with self.lock:
            # Initialize bucket if new
            if ip not in self.buckets:
                self.buckets[ip] = (self.capacity, now)
            
            tokens, last_update = self.buckets[ip]
            
            # Refill tokens
            elapsed = now - last_update
            new_tokens = elapsed * self.rate
            tokens = min(self.capacity, tokens + new_tokens)
            
            # Check availability
            if tokens >= 1.0:
                self.buckets[ip] = (tokens - 1.0, now)
                return True
            else:
                self.buckets[ip] = (tokens, now)
                return False

class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI Middleware for Rate Limiting."""
    
    def __init__(self, app, limiter: RateLimiter):
        super().__init__(app)
        self.limiter = limiter
    
    async def dispatch(self, request: Request, call_next):
        # Skip health checks
        if request.url.path == "/health" or request.url.path == "/metrics":
            return await call_next(request)
            
        client_ip = request.client.host if request.client else "unknown"
        
        if not self.limiter.check_limit(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please slow down."}
            )
        
        response = await call_next(request)
        return response
