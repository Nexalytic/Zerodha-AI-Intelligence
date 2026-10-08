from __future__ import annotations

from typing import Any

from app.models.portfolio import Holding


def analyze_portfolio(holdings: list[Holding]) -> dict[str, Any]:
    invested_value = sum(h.quantity * h.average_price for h in holdings)
    market_value = sum(h.quantity * h.current_price for h in holdings)
    pnl = market_value - invested_value
    pnl_percent = (pnl / invested_value * 100) if invested_value else 0.0

    total_market = market_value or 1.0
    weights = [
        (h.quantity * h.current_price) / total_market
        for h in holdings
    ]
    hhi = sum(weight**2 for weight in weights)

    holding_rows = [
        {
            "symbol": h.symbol,
            "sector": h.sector,
            "quantity": h.quantity,
            "average_price": h.average_price,
            "current_price": h.current_price,
            "invested_value": round(h.quantity * h.average_price, 2),
            "market_value": round(h.quantity * h.current_price, 2),
            "pnl": round(
                h.quantity * (h.current_price - h.average_price),
                2,
            ),
            "day_change_percent": h.day_change_percent,
        }
        for h in holdings
    ]

    return {
        "summary": {
            "invested_value": round(invested_value, 2),
            "market_value": round(market_value, 2),
            "pnl": round(pnl, 2),
            "pnl_percent": round(pnl_percent, 2),
            "holding_count": len(holdings),
            "hhi": round(hhi, 4),
        },
        "holdings": holding_rows,
    }
def calculate_contribution_analysis(
    holdings: list[dict],
) -> list[dict]:
    contributions = []

    total_pnl = sum(
        float(holding["quantity"])
        * (
            float(holding["current_price"])
            - float(holding["average_price"])
        )
        for holding in holdings
    )

    for holding in holdings:
        quantity = float(holding["quantity"])
        average_price = float(holding["average_price"])
        current_price = float(holding["current_price"])

        pnl = quantity * (current_price - average_price)

        contribution_percent = (
            (pnl / total_pnl) * 100
            if total_pnl != 0
            else 0.0
        )

        contributions.append(
            {
                "symbol": holding["symbol"],
                "pnl": pnl,
                "contribution_percent": contribution_percent,
            }
        )

    return contributions
def calculate_portfolio_historical_values(
    holdings: list[dict],
    historical_prices: dict[str, list[dict]],
) -> list[dict]:
    price_series: dict[str, dict[str, float]] = {}

    for symbol, rows in historical_prices.items():
        price_series[symbol] = {
            row["date"]: float(row["close"])
            for row in rows
        }

    if not price_series:
        return []

    common_dates = set.intersection(
        *[set(series.keys()) for series in price_series.values()]
    )

    if not common_dates:
        return []

    result: list[dict] = []

    for date in sorted(common_dates):
        portfolio_value = 0.0

        for holding in holdings:
            symbol = holding["symbol"]
            quantity = float(holding["quantity"])

            if symbol not in price_series:
                continue

            close = price_series[symbol].get(date)

            if close is not None:
                portfolio_value += quantity * close

        result.append(
            {
                "date": date,
                "portfolio_value": portfolio_value,
            }
        )

    return result
def calculate_portfolio_historical_returns(
    portfolio_values: list[dict],
) -> list[dict]:
    ordered = sorted(
        portfolio_values,
        key=lambda row: row["date"],
    )

    returns: list[dict] = []

    for index in range(1, len(ordered)):
        previous_value = float(
            ordered[index - 1]["portfolio_value"]
        )
        current_value = float(
            ordered[index]["portfolio_value"]
        )

        daily_return = (
            (current_value - previous_value) / previous_value
            if previous_value
            else 0.0
        )

        returns.append(
            {
                "date": ordered[index]["date"],
                "portfolio_value": current_value,
                "previous_portfolio_value": previous_value,
                "return": daily_return,
                "return_percent": daily_return * 100,
            }
        )

    return returns
def calculate_structured_analytics(
    holdings: list[dict],
    historical_prices: dict[str, list[dict]],
    benchmark_prices: list[dict],
    benchmark_symbol: str = "NIFTYBEES.BSE",
) -> dict:
    from app.analytics.market_analytics import (
        calculate_benchmark_comparison,
        calculate_cumulative_return,
        calculate_portfolio_growth,
        calculate_returns,
    )
    from app.analytics.risk_analytics import (
        calculate_beta,
        calculate_correlation,
        calculate_max_drawdown,
        calculate_sharpe,
        calculate_volatility,
    )

    portfolio_values = calculate_portfolio_historical_values(
        holdings,
        historical_prices,
    )

    portfolio_returns = calculate_portfolio_historical_returns(
        portfolio_values,
    )

    benchmark_returns = calculate_returns(
        benchmark_prices,
    )

    benchmark_comparison = calculate_benchmark_comparison(
        portfolio_returns,
        benchmark_returns,
        "PORTFOLIO",
        benchmark_symbol,
    )

    return {
        "risk": {
            "historical_volatility": calculate_volatility(
                portfolio_returns
            ),
            "maximum_drawdown": calculate_max_drawdown(
                portfolio_values,
                value_key="portfolio_value",
            ),
            "sharpe_ratio": calculate_sharpe(
                portfolio_returns
            ),
            "beta": calculate_beta(
                portfolio_returns,
                benchmark_returns,
            ),
            "correlation": calculate_correlation(
                portfolio_returns,
                benchmark_returns,
            ),
        },
        "performance": {
            "daily_return": (
                portfolio_returns[-1]["return"]
                if portfolio_returns
                else 0.0
            ),
            "cumulative_return": calculate_cumulative_return(
                portfolio_returns
            ),
            "portfolio_growth": calculate_portfolio_growth(
                portfolio_returns
            ),
            "benchmark_performance": {
                "symbol": benchmark_symbol,
                "cumulative_return": (
                    benchmark_comparison["benchmark_return"]
                ),
            },
        },
        "benchmark_comparison": benchmark_comparison,
        "contribution_analysis": calculate_contribution_analysis(
            holdings
        ),
    }