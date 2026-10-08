from __future__ import annotations

import asyncio

from dotenv import load_dotenv

from app.models.tool import ToolResponse
from app.services.market_service import get_market_quote


load_dotenv()

_alpha_quote_lock = asyncio.Lock()


async def get_quote(symbol: str) -> ToolResponse:
    result = await get_market_quote(symbol, _alpha_quote_lock)

    return ToolResponse(
        tool="get_quote",
        status="success",
        data=result,
    )