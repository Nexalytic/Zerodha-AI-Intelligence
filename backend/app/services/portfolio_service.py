from __future__ import annotations

from typing import Any

from app.analytics.portfolio_analytics import analyze_portfolio as analyze_portfolio_analytics
from app.models.portfolio import Holding


def analyze_portfolio(holdings: list[Holding]) -> dict[str, Any]:
    return analyze_portfolio_analytics(holdings)