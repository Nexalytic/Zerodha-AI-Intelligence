import pytest

from app.analytics.market_analytics import (
    calculate_benchmark_comparison,
    calculate_cumulative_return,
    calculate_portfolio_growth,
    calculate_returns,
)


def test_calculate_returns():
    rows = [
        {"date": "2026-01-02", "close": 110},
        {"date": "2026-01-01", "close": 100},
        {"date": "2026-01-03", "close": 121},
    ]

    result = calculate_returns(rows)

    assert len(result) == 2

    assert result[0]["date"] == "2026-01-02"
    assert result[0]["close"] == 110.0
    assert result[0]["previous_close"] == 100.0
    assert result[0]["return"] == pytest.approx(0.10)
    assert result[0]["return_percent"] == pytest.approx(10.0)

    assert result[1]["date"] == "2026-01-03"
    assert result[1]["return"] == pytest.approx(0.10)
    assert result[1]["return_percent"] == pytest.approx(10.0)


def test_calculate_cumulative_return():
    returns = [
        {"date": "2026-01-02", "return": 0.10},
        {"date": "2026-01-03", "return": 0.10},
    ]

    result = calculate_cumulative_return(returns)

    assert result == pytest.approx(0.21)


def test_calculate_benchmark_comparison():
    portfolio_returns = [
        {"date": "2026-01-02", "return": 0.10},
        {"date": "2026-01-03", "return": 0.10},
    ]

    benchmark_returns = [
        {"date": "2026-01-02", "return": 0.05},
        {"date": "2026-01-03", "return": 0.05},
    ]

    result = calculate_benchmark_comparison(
        portfolio_returns,
        benchmark_returns,
        "PORTFOLIO",
        "NIFTYBEES.BSE",
    )

    assert result["portfolio_symbol"] == "PORTFOLIO"
    assert result["benchmark_symbol"] == "NIFTYBEES.BSE"
    assert result["common_dates"] == 2
    assert result["start_date"] == "2026-01-02"
    assert result["end_date"] == "2026-01-03"

    assert result["portfolio_return"] == pytest.approx(0.21)
    assert result["benchmark_return"] == pytest.approx(0.1025)
    assert result["relative_return"] == pytest.approx(0.1075)


def test_calculate_portfolio_growth():
    returns = [
        {"date": "2026-01-02", "return": 0.10},
        {"date": "2026-01-03", "return": 0.10},
    ]

    result = calculate_portfolio_growth(
        returns,
        initial_value=100.0,
    )

    assert len(result) == 2

    assert result[0]["date"] == "2026-01-02"
    assert result[0]["daily_return"] == pytest.approx(0.10)
    assert result[0]["growth"] == pytest.approx(110.0)

    assert result[1]["date"] == "2026-01-03"
    assert result[1]["daily_return"] == pytest.approx(0.10)
    assert result[1]["growth"] == pytest.approx(121.0)
