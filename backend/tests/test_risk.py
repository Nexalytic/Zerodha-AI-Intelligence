import pytest

from app.analytics.risk_analytics import (
    calculate_beta,
    calculate_correlation,
    calculate_max_drawdown,
    calculate_sharpe,
    calculate_volatility,
)


def test_calculate_volatility():
    returns = [
        {"date": "2026-01-01", "return": 0.01},
        {"date": "2026-01-02", "return": 0.02},
        {"date": "2026-01-03", "return": 0.03},
    ]

    result = calculate_volatility(
        returns,
        annualization_factor=252,
    )

    expected_daily_volatility = 0.01
    expected_annualized = (
        expected_daily_volatility * (252 ** 0.5)
    )

    assert result == pytest.approx(expected_annualized)


def test_calculate_max_drawdown():
    rows = [
        {"date": "2026-01-01", "close": 100},
        {"date": "2026-01-02", "close": 120},
        {"date": "2026-01-03", "close": 90},
        {"date": "2026-01-04", "close": 110},
    ]

    result = calculate_max_drawdown(rows)

    assert result == pytest.approx(-0.25)


def test_calculate_sharpe():
    returns = [
        {"date": "2026-01-01", "return": 0.01},
        {"date": "2026-01-02", "return": 0.02},
        {"date": "2026-01-03", "return": 0.03},
    ]

    result = calculate_sharpe(
        returns,
        risk_free_rate=0.0,
        annualization_factor=252,
    )

    expected_daily_mean = 0.02
    expected_daily_volatility = 0.01
    expected_sharpe = (
        expected_daily_mean
        / expected_daily_volatility
        * (252 ** 0.5)
    )

    assert result == pytest.approx(expected_sharpe)


def test_calculate_beta():
    portfolio_returns = [
        {"date": "2026-01-01", "return": 0.02},
        {"date": "2026-01-02", "return": 0.04},
        {"date": "2026-01-03", "return": 0.06},
    ]

    benchmark_returns = [
        {"date": "2026-01-01", "return": 0.01},
        {"date": "2026-01-02", "return": 0.02},
        {"date": "2026-01-03", "return": 0.03},
    ]

    result = calculate_beta(
        portfolio_returns,
        benchmark_returns,
    )

    assert result == pytest.approx(2.0)


def test_calculate_correlation():
    portfolio_returns = [
        {"date": "2026-01-01", "return": 0.02},
        {"date": "2026-01-02", "return": 0.04},
        {"date": "2026-01-03", "return": 0.06},
    ]

    benchmark_returns = [
        {"date": "2026-01-01", "return": 0.01},
        {"date": "2026-01-02", "return": 0.02},
        {"date": "2026-01-03", "return": 0.03},
    ]

    result = calculate_correlation(
        portfolio_returns,
        benchmark_returns,
    )

    assert result == pytest.approx(1.0)


def test_risk_functions_handle_insufficient_data():
    returns = [{"date": "2026-01-01", "return": 0.05}]

    assert calculate_volatility(returns) == 0.0
    assert calculate_sharpe(returns) == 0.0

    portfolio_returns = [
        {"date": "2026-01-01", "return": 0.05},
    ]

    benchmark_returns = [
        {"date": "2026-01-01", "return": 0.03},
    ]

    assert calculate_beta(
        portfolio_returns,
        benchmark_returns,
    ) == 0.0

    assert calculate_correlation(
        portfolio_returns,
        benchmark_returns,
    ) == 0.0
