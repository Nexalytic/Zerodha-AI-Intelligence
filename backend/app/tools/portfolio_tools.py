from __future__ import annotations

from typing import Any

from app.demo_store import load_portfolio
from app.models.portfolio import Holding
from app.models.tool import ToolResponse


def _resolve_holdings(
    user: str,
    holdings: list[Holding] | None = None,
) -> list[Holding]:
    if holdings is not None:
        return holdings

    raw_holdings = load_portfolio(user)
    return [Holding.model_validate(item) for item in raw_holdings]


def get_portfolio(
    user: str,
    holdings: list[Holding] | None = None,
) -> ToolResponse:
    resolved_holdings = _resolve_holdings(user, holdings)

    return ToolResponse(
        tool="get_portfolio",
        status="success",
        data={
            "holdings": [
                holding.model_dump() for holding in resolved_holdings
            ],
            "count": len(resolved_holdings),
        },
    )


def calculate_portfolio_metrics(
    user: str,
    holdings: list[Holding] | None = None,
) -> ToolResponse:
    resolved_holdings = _resolve_holdings(user, holdings)

    from app.services.portfolio_service import analyze_portfolio

    result = analyze_portfolio(resolved_holdings)

    return ToolResponse(
        tool="calculate_portfolio_metrics",
        status="success",
        data=result,
    )
