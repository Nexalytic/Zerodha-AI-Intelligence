from __future__ import annotations

import math
from typing import Any


def calculate_volatility(
    returns: list[dict[str, Any]],
    annualization_factor: int = 252,
) -> float:
    values = [float(row["return"]) for row in returns]

    if len(values) < 2:
        return 0.0

    mean_return = sum(values) / len(values)

    variance = sum(
        (value - mean_return) ** 2
        for value in values
    ) / (len(values) - 1)

    daily_volatility = math.sqrt(variance)

    return daily_volatility * math.sqrt(annualization_factor)
def calculate_max_drawdown(
    rows: list[dict[str, Any]],
    value_key: str = "close",
) -> float:
    ordered = sorted(rows, key=lambda row: row["date"])

    if not ordered:
        return 0.0

    peak = float(ordered[0][value_key])
    max_drawdown = 0.0

    for row in ordered:
        value = float(row[value_key])

        if value > peak:
            peak = value

        drawdown = (
            (value - peak) / peak
            if peak
            else 0.0
        )

        if drawdown < max_drawdown:
            max_drawdown = drawdown

    return max_drawdown
def calculate_sharpe(
    returns: list[dict[str, Any]],
    risk_free_rate: float = 0.0,
    annualization_factor: int = 252,
) -> float:
    values = [float(row["return"]) for row in returns]

    if len(values) < 2:
        return 0.0

    daily_risk_free_rate = (
        (1 + risk_free_rate) ** (1 / annualization_factor) - 1
    )

    excess_returns = [
        value - daily_risk_free_rate
        for value in values
    ]

    mean_excess_return = sum(excess_returns) / len(excess_returns)

    variance = sum(
        (value - mean_excess_return) ** 2
        for value in excess_returns
    ) / (len(excess_returns) - 1)

    daily_volatility = math.sqrt(variance)

    if daily_volatility == 0:
        return 0.0

    return (
        mean_excess_return
        / daily_volatility
        * math.sqrt(annualization_factor)
    )
def calculate_beta(
    portfolio_returns: list[dict[str, Any]],
    benchmark_returns: list[dict[str, Any]],
) -> float:
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

    if len(common_dates) < 2:
        return 0.0

    portfolio_values = [
        portfolio_by_date[date]
        for date in common_dates
    ]
    benchmark_values = [
        benchmark_by_date[date]
        for date in common_dates
    ]

    benchmark_mean = sum(benchmark_values) / len(benchmark_values)
    portfolio_mean = sum(portfolio_values) / len(portfolio_values)

    covariance = sum(
        (portfolio_value - portfolio_mean)
        * (benchmark_value - benchmark_mean)
        for portfolio_value, benchmark_value
        in zip(portfolio_values, benchmark_values)
    ) / (len(common_dates) - 1)

    benchmark_variance = sum(
        (value - benchmark_mean) ** 2
        for value in benchmark_values
    ) / (len(common_dates) - 1)

    if benchmark_variance == 0:
        return 0.0

    return covariance / benchmark_variance
def calculate_correlation(
    portfolio_returns: list[dict[str, Any]],
    benchmark_returns: list[dict[str, Any]],
) -> float:
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

    if len(common_dates) < 2:
        return 0.0

    portfolio_values = [
        portfolio_by_date[date]
        for date in common_dates
    ]
    benchmark_values = [
        benchmark_by_date[date]
        for date in common_dates
    ]

    portfolio_mean = sum(portfolio_values) / len(portfolio_values)
    benchmark_mean = sum(benchmark_values) / len(benchmark_values)

    portfolio_deviations = [
        value - portfolio_mean
        for value in portfolio_values
    ]
    benchmark_deviations = [
        value - benchmark_mean
        for value in benchmark_values
    ]

    covariance = sum(
        portfolio_deviation * benchmark_deviation
        for portfolio_deviation, benchmark_deviation
        in zip(portfolio_deviations, benchmark_deviations)
    )

    portfolio_variance = sum(
        deviation ** 2
        for deviation in portfolio_deviations
    )

    benchmark_variance = sum(
        deviation ** 2
        for deviation in benchmark_deviations
    )

    denominator = math.sqrt(
        portfolio_variance * benchmark_variance
    )

    if denominator == 0:
        return 0.0

    return covariance / denominator