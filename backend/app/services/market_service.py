from __future__ import annotations

import asyncio
import os
import re
import time
from datetime import date
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

from app.demo_store import (
    alpha_usage,
    load_market_prices,
    load_quote,
    record_alpha_request,
    save_market_prices,
    save_quote,
)


async def get_market_quote(
    symbol: str,
    alpha_quote_lock: asyncio.Lock,
) -> dict[str, Any]:
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "").strip()

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Set ALPHA_VANTAGE_API_KEY in backend/.env to enable market quotes.",
        )

    original = symbol.strip().upper()

    if not re.fullmatch(r"[A-Z0-9._-]{1,32}", original):
        raise HTTPException(
            status_code=422,
            detail="Enter one ticker symbol, such as INFY or IBM.",
        )

    # Bare symbols in this India-focused demo map to Alpha Vantage's documented BSE suffix.
    av_symbol = original if "." in original else f"{original}.BSE"

    cache_seconds = max(
        60,
        int(os.getenv("ALPHA_VANTAGE_CACHE_SECONDS", "900")),
    )

    cached = load_quote(av_symbol, cache_seconds)

    if cached:
        return {
            "quote": {**cached, "symbol": original},
            "provider_symbol": av_symbol,
            "source": "Alpha Vantage",
            "freshness": "cached quote",
        }

    today = date.today().isoformat()

    async with alpha_quote_lock:
        # Recheck after acquiring the lock to avoid duplicate calls from overlapping tabs.
        cached = load_quote(av_symbol, cache_seconds)

        if cached:
            return {
                "quote": {**cached, "symbol": original},
                "provider_symbol": av_symbol,
                "source": "Alpha Vantage",
                "freshness": "cached quote",
            }

        count, last_request = alpha_usage(today)

        if count >= int(os.getenv("ALPHA_VANTAGE_DAILY_LIMIT", "25")):
            raise HTTPException(
                status_code=429,
                detail=(
                    "Alpha Vantage's configured daily request budget is used up. "
                    "Cached quotes remain available; try again tomorrow or adjust "
                    "your provider plan and local limit."
                ),
            )

        min_interval = max(
            0.0,
            float(os.getenv("ALPHA_VANTAGE_MIN_INTERVAL_SECONDS", "12.1")),
        )

        wait = min_interval - (time.time() - last_request)

        if wait > 0:
            await asyncio.sleep(wait)

        record_alpha_request(today, time.time())

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(
                    os.getenv(
                        "ALPHA_VANTAGE_BASE_URL",
                        "https://www.alphavantage.co/query",
                    ),
                    params={
                        "function": "GLOBAL_QUOTE",
                        "symbol": av_symbol,
                        "apikey": api_key,
                    },
                )

                response.raise_for_status()

            data = response.json()

        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Alpha Vantage quote request failed. "
                    "Check connectivity and the API key."
                ),
            ) from exc

        if data.get("Note") or data.get("Information"):
            raise HTTPException(
                status_code=429,
                detail=(
                    "Alpha Vantage rate limit or plan limit reached. "
                    "Wait before requesting another quote."
                ),
            )

        if data.get("Error Message"):
            raise HTTPException(
                status_code=422,
                detail=(
                    "Alpha Vantage does not recognize this ticker. "
                    "Try its exchange suffix, for example RELIANCE.BSE."
                ),
            )

        raw = data.get("Global Quote") or {}

        if not raw.get("05. price"):
            raise HTTPException(
                status_code=404,
                detail=(
                    "Alpha Vantage returned no quote for this symbol. "
                    "Check its exchange suffix and data entitlement."
                ),
            )

        try:
            last = float(raw["05. price"])
            previous = float(raw.get("08. previous close") or 0)

            quote = {
                "symbol": original,
                "last_price": last,
                "previous_close": previous,
                "change_percent": float(
                    str(raw.get("10. change percent", "0%"))
                    .replace("%", "")
                    or 0
                ),
                "volume": int(raw.get("06. volume") or 0),
                "high": float(raw.get("03. high") or 0),
                "low": float(raw.get("04. low") or 0),
                "timestamp": raw.get("07. latest trading day"),
                "retrieved_at": time.time(),
                "cached": False,
            }

        except (TypeError, ValueError, KeyError) as exc:
            raise HTTPException(
                status_code=502,
                detail="Alpha Vantage returned an unexpected quote format.",
            ) from exc

        save_quote(av_symbol, quote)

    return {
        "quote": quote,
        "provider_symbol": av_symbol,
        "source": "Alpha Vantage",
        "freshness": (
            "latest available; global quotes default to end-of-day "
            "outside entitled US realtime/delayed data"
        ),
    }
async def get_historical_prices(
    symbol: str,
    alpha_quote_lock: asyncio.Lock,
    outputsize: str = "compact",
) -> dict[str, Any]:
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "").strip()

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Set ALPHA_VANTAGE_API_KEY in backend/.env to enable historical prices.",
        )

    original = symbol.strip().upper()

    if not re.fullmatch(r"[A-Z0-9._-]{1,32}", original):
        raise HTTPException(
            status_code=422,
            detail="Enter one ticker symbol, such as INFY or IBM.",
        )

    av_symbol = original if "." in original else f"{original}.BSE"

    if outputsize not in {"compact", "full"}:
        raise HTTPException(
            status_code=422,
            detail="outputsize must be compact or full.",
        )

    today = date.today().isoformat()

    async with alpha_quote_lock:
        count, last_request = alpha_usage(today)

        if count >= int(os.getenv("ALPHA_VANTAGE_DAILY_LIMIT", "25")):
            raise HTTPException(
                status_code=429,
                detail="Alpha Vantage's configured daily request budget is used up.",
            )

        min_interval = max(
            0.0,
            float(os.getenv("ALPHA_VANTAGE_MIN_INTERVAL_SECONDS", "12.1")),
        )

        wait = min_interval - (time.time() - last_request)

        if wait > 0:
            await asyncio.sleep(wait)

        record_alpha_request(today, time.time())

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    os.getenv(
                        "ALPHA_VANTAGE_BASE_URL",
                        "https://www.alphavantage.co/query",
                    ),
                    params={
                        "function": "TIME_SERIES_DAILY",
                        "symbol": av_symbol,
                        "outputsize": outputsize,
                        "apikey": api_key,
                    },
                )

                response.raise_for_status()

            data = response.json()

        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(
                status_code=502,
                detail="Historical Alpha Vantage request failed.",
            ) from exc

        if data.get("Note") or data.get("Information"):
            raise HTTPException(
                status_code=429,
                detail="Alpha Vantage rate limit or plan limit reached.",
            )

        if data.get("Error Message"):
            raise HTTPException(
                status_code=422,
                detail="Alpha Vantage does not recognize this ticker.",
            )

        series = data.get("Time Series (Daily)") or {}

        if not series:
            raise HTTPException(
                status_code=404,
                detail="Alpha Vantage returned no historical data for this symbol.",
            )

        fetched_at = time.time()
        rows: list[dict[str, Any]] = []

        try:
            for trading_date, values in series.items():
                rows.append(
                    {
                        "symbol": original,
                        "date": trading_date,
                        "open": float(values["1. open"]),
                        "high": float(values["2. high"]),
                        "low": float(values["3. low"]),
                        "close": float(values["4. close"]),
                        "volume": float(values["5. volume"]),
                        "source": "Alpha Vantage",
                        "fetched_at": fetched_at,
                    }
                )
        except (TypeError, ValueError, KeyError) as exc:
            raise HTTPException(
                status_code=502,
                detail="Alpha Vantage returned an unexpected historical data format.",
            ) from exc

        save_market_prices(rows)

    return {
        "symbol": original,
        "provider_symbol": av_symbol,
        "source": "Alpha Vantage",
        "count": len(rows),
        "data": rows,
    }