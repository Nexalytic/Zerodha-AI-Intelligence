from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Query

from app.services.market_service import (
    get_historical_prices,
    get_market_quote,
)

router = APIRouter(prefix="/api/v1/market", tags=["market"])

_alpha_quote_lock = asyncio.Lock()


@router.get("/quotes")
async def market_quote(
    symbol: str = Query(min_length=1, max_length=32),
) -> dict[str, Any]:
    return await get_market_quote(symbol, _alpha_quote_lock)


@router.get("/historical")
async def market_historical(
    symbol: str = Query(min_length=1, max_length=32),
    outputsize: str = Query(default="compact"),
) -> dict[str, Any]:
    return await get_historical_prices(
        symbol,
        _alpha_quote_lock,
        outputsize,
    )