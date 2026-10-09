from __future__ import annotations

import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()


def _validate_runtime_config() -> None:
    if os.getenv("APP_ENV", "development").lower() == "production":
        raise RuntimeError(
            "This is a local demo without authentication or production security. "
            "Do not run it in production."
        )


_validate_runtime_config()

from app.api.ai import router as ai_router
from app.api.activity import router as activity_router
from app.api.operations import router as operations_router
from app.api.market import router as market_router
from app.api.portfolio import router as portfolio_router
from app.api.watchlist import router as watchlist_router


production = os.getenv("APP_ENV", "development").lower() == "production"

app = FastAPI(
    title="Zerodha AI Intelligence API",
    version="1.0.0",
    docs_url=None if production else "/api/docs",
    openapi_url=None if production else "/api/openapi.json",
)
@app.middleware("http")
async def observe_requests(request: Request, call_next):
    import time

    started_at = time.perf_counter()
    error_message = None
    response = None
    should_record = request.url.path.startswith("/api/")

    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        error_message = str(exc)
        raise
    finally:
        if should_record:
            duration_ms = (time.perf_counter() - started_at) * 1000

            try:
                from app.demo_store import record_api_request

                record_api_request(
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code if response else 500,
                    duration_ms=duration_ms,
                    error=error_message,
                )
            except Exception:
                # Observability must never break the application.
                pass


origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,https://euphonious-kringle-abd2bf.netlify.app",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "zerodha-ai-demo-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


app.include_router(market_router)
app.include_router(portfolio_router)
app.include_router(watchlist_router)
app.include_router(ai_router)
app.include_router(activity_router)
app.include_router(operations_router)