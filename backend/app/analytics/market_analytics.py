from __future__ import annotations

from typing import Any


def calculate_returns(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda row: row["date"])

    returns: list[dict[str, Any]] = []

    for index in range(1, len(ordered)):
        previous_close = float(ordered[index - 1]["close"])
        current_close = float(ordered[index]["close"])

        daily_return = (
            (current_close - previous_close) / previous_close
            if previous_close
            else 0.0
        )

        returns.append(
            {
                "date": ordered[index]["date"],
                "close": current_close,
                "previous_close": previous_close,
                "return": daily_return,
                "return_percent": daily_return * 100,
            }
        )

    return returns
def calculate_cumulative_return(
    returns: list[dict[str, Any]],
) -> float:
    cumulative_growth = 1.0

    for row in returns:
        cumulative_growth *= 1 + float(row["return"])

    return cumulative_growth - 1
def calculate_benchmark_comparison(
    portfolio_returns: list[dict[str, Any]],
    benchmark_returns: list[dict[str, Any]],
    portfolio_symbol: str = "PORTFOLIO",
    benchmark_symbol: str = "BENCHMARK",
) -> dict[str, Any]:
    portfolio_by_date = {
        row["date"]: float(row["return"])
        for row in portfolio_returns
    }
    benchmark_by_date = {
        row["date"]: float(row["return"])
        for row in benchmark_returns
    }

    common_dates = sorted(
        set(portfolio_by_date) & set(benchmark_by_date)
    )

    if not common_dates:
        return {
            "portfolio_symbol": portfolio_symbol,
            "benchmark_symbol": benchmark_symbol,
            "common_dates": 0,
            "portfolio_return": 0.0,
            "benchmark_return": 0.0,
            "relative_return": 0.0,
        }

    aligned_portfolio = [
        {
            "date": date,
            "return": portfolio_by_date[date],
        }
        for date in common_dates
    ]

    aligned_benchmark = [
        {
            "date": date,
            "return": benchmark_by_date[date],
        }
        for date in common_dates
    ]

    portfolio_return = calculate_cumulative_return(aligned_portfolio)
    benchmark_return = calculate_cumulative_return(aligned_benchmark)

    return {
        "portfolio_symbol": portfolio_symbol,
        "benchmark_symbol": benchmark_symbol,
        "start_date": common_dates[0],
        "end_date": common_dates[-1],
        "common_dates": len(common_dates),
        "portfolio_return": portfolio_return,
        "benchmark_return": benchmark_return,
        "relative_return": portfolio_return - benchmark_return,
    }
def calculate_portfolio_growth(
    returns: list[dict[str, Any]],
    initial_value: float = 1.0,
) -> list[dict[str, Any]]:
    ordered = sorted(
        returns,
        key=lambda row: row["date"],
    )

    growth = initial_value
    result: list[dict[str, Any]] = []

    for row in ordered:
        daily_return = float(row["return"])
        growth *= 1 + daily_return

        result.append(
            {
                "date": row["date"],
                "daily_return": daily_return,
                "growth": growth,
            }
        )

    return result