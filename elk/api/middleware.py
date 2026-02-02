"""
ELK Server - Production Middleware
Implements FastAPI best practices:
- Structured JSONL logging
- Request timing metrics
- Correlation IDs
- Error handling with traces
"""

import time
import uuid
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from elk.core.config import settings


class StructuredLogger:
    """
    JSONL logger for production observability.
    Writes to logs/requests.jsonl per MASTER_VISION Part 5.
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Daily rotation
        today = datetime.now().strftime("%Y-%m-%d")
        self.request_log = self.log_dir / f"requests_{today}.jsonl"
        self.error_log = self.log_dir / f"errors_{today}.jsonl"
        
    def log_request(self, data: dict) -> None:
        """Log request to JSONL file."""
        with open(self.request_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, default=str) + '\n')
    
    def log_error(self, data: dict) -> None:
        """Log error to separate JSONL file."""
        with open(self.error_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, default=str) + '\n')


# Global logger instance
_logger = StructuredLogger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request/response logging with metrics.
    
    Captures:
    - Request timing (latency_ms)
    - Status codes
    - Correlation IDs for tracing
    - Request path and method
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate correlation ID for request tracing
        correlation_id = str(uuid.uuid4())[:8]
        request.state.correlation_id = correlation_id
        
        # Start timing
        start_time = time.perf_counter()
        
        # Process request
        response = await call_next(request)
        
        # Calculate latency
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        # Log request
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "correlation_id": correlation_id,
            "method": request.method,
            "path": str(request.url.path),
            "status_code": response.status_code,
            "latency_ms": round(latency_ms, 2),
            "client_ip": request.client.host if request.client else "unknown"
        }
        
        # Add to response headers for tracing
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Latency-MS"] = str(round(latency_ms, 2))
        
        # Log based on status
        if response.status_code >= 400:
            _logger.log_error(log_entry)
        else:
            _logger.log_request(log_entry)
        
        return response


class MetricsCollector:
    """
    In-memory metrics collector for KPI tracking.
    Aligns with PRD KPIs: 98% validation, Human Override <15%
    """
    
    def __init__(self):
        self._metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "validation_errors": 0,
            "total_latency_ms": 0.0,
            "min_latency_ms": float('inf'),
            "max_latency_ms": 0.0,
            "human_reviews_triggered": 0,
            "auto_dispatched": 0
        }
    
    def record_request(self, success: bool, latency_ms: float):
        """Record request metrics."""
        self._metrics["total_requests"] += 1
        if success:
            self._metrics["successful_requests"] += 1
        else:
            self._metrics["failed_requests"] += 1
        
        self._metrics["total_latency_ms"] += latency_ms
        self._metrics["min_latency_ms"] = min(self._metrics["min_latency_ms"], latency_ms)
        self._metrics["max_latency_ms"] = max(self._metrics["max_latency_ms"], latency_ms)
    
    def record_validation_error(self):
        """Record validation error for KPI tracking."""
        self._metrics["validation_errors"] += 1
    
    def record_human_review(self):
        """Track human review triggers."""
        self._metrics["human_reviews_triggered"] += 1
    
    def record_auto_dispatch(self):
        """Track successful auto-dispatches."""
        self._metrics["auto_dispatched"] += 1
    
    def get_metrics(self) -> dict:
        """Get current metrics with computed KPIs."""
        total = max(self._metrics["total_requests"], 1)
        dispatched = self._metrics["auto_dispatched"] + self._metrics["human_reviews_triggered"]
        
        min_lat = self._metrics["min_latency_ms"]
        if min_lat == float('inf'):
            min_lat = 0.0
            
        return {
            **self._metrics,
            "min_latency_ms": min_lat,
            "avg_latency_ms": round(self._metrics["total_latency_ms"] / total, 2),
            "success_rate": round(self._metrics["successful_requests"] / total, 4),
            "validation_pass_rate": round(1 - (self._metrics["validation_errors"] / total), 4),
            "human_override_rate": round(
                self._metrics["human_reviews_triggered"] / max(dispatched, 1), 4
            )
        }


# Global metrics instance
metrics = MetricsCollector()


def create_exception_handlers(app: FastAPI):
    """
    Register custom exception handlers.
    Best practice: detailed error responses with correlation IDs.
    """
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors with detailed feedback."""
        metrics.record_validation_error()
        
        correlation_id = getattr(request.state, 'correlation_id', 'unknown')
        
        error_detail = {
            "correlation_id": correlation_id,
            "error_type": "validation_error",
            "detail": exc.errors(),
            "timestamp": datetime.now().isoformat()
        }
        
        _logger.log_error({
            **error_detail,
            "path": str(request.url.path),
            "body_preview": str(exc.body)[:500] if exc.body else None
        })
        
        return JSONResponse(
            status_code=422,
            content=error_detail
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions with structured response."""
        correlation_id = getattr(request.state, 'correlation_id', 'unknown')
        
        error_detail = {
            "correlation_id": correlation_id,
            "error_type": "http_error",
            "status_code": exc.status_code,
            "detail": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
        
        _logger.log_error(error_detail)
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_detail
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions with trace."""
        import traceback
        
        correlation_id = getattr(request.state, 'correlation_id', 'unknown')
        
        error_detail = {
            "correlation_id": correlation_id,
            "error_type": "server_error",
            "detail": str(exc),
            "trace": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }
        
        _logger.log_error(error_detail)
        
        # Don't expose trace in response
        return JSONResponse(
            status_code=500,
            content={
                "correlation_id": correlation_id,
                "error_type": "server_error",
                "detail": "Internal server error. Check logs with correlation_id.",
                "timestamp": datetime.now().isoformat()
            }
        )


def setup_production_middleware(app: FastAPI):
    """
    Configure all production middleware and handlers.
    Call this in app.py after creating FastAPI instance.
    """
    # Rate Limiting (D2 Optimization)
    try:
        from .limiter import RateLimitMiddleware, RateLimiter
        # Limit to 5 requests/sec burst 20 (configurable)
        limiter = RateLimiter(rate=5.0, capacity=20)
        app.add_middleware(RateLimitMiddleware, limiter=limiter)
    except ImportError:
        logging.warning("RateLimiter not available")

    # CORS Protection
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Trust specific hosts (security best practice)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

    # Compress large responses
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Add logging middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    # Register exception handlers
    create_exception_handlers(app)
    
    # Add metrics endpoint
    @app.get("/metrics")
    async def get_metrics():
        """
        Prometheus-style metrics endpoint.
        Returns current KPIs per PRD Section 4.
        """
        return metrics.get_metrics()
    
    return app
