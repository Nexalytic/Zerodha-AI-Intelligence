from __future__ import annotations

from collections import defaultdict

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


def calculate_sector_allocation(
    user: str,
    holdings: list[Holding] | None = None,
) -> ToolResponse:
    resolved_holdings = _resolve_holdings(user, holdings)

    total_market_value = sum(
        holding.quantity * holding.current_price
        for holding in resolved_holdings
    )

    allocation: dict[str, float] = defaultdict(float)

    for holding in resolved_holdings:
        allocation[holding.sector] += (
            holding.quantity * holding.current_price
        )

    sectors = {
        sector: round(
            (value / total_market_value * 100)
            if total_market_value
            else 0.0,
            2,
        )
        for sector, value in allocation.items()
    }

    return ToolResponse(
        tool="calculate_sector_allocation",
        status="success",
        data={
            "total_market_value": round(total_market_value, 2),
            "sectors": sectors,
        },
    )


def calculate_concentration(
    user: str,
    holdings: list[Holding] | None = None,
) -> ToolResponse:
    resolved_holdings = _resolve_holdings(user, holdings)

    from app.services.portfolio_service import analyze_portfolio

    result = analyze_portfolio(resolved_holdings)
    summary = result["summary"]

    return ToolResponse(
        tool="calculate_concentration",
        status="success",
        data={
            "hhi": summary["hhi"],
            "holding_count": summary["holding_count"],
        },
    )