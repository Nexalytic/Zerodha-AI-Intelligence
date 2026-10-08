import pytest

from app.analytics.portfolio_analytics import (
    analyze_portfolio,
    calculate_contribution_analysis,
    calculate_portfolio_historical_values,
    calculate_portfolio_historical_returns,
)
from app.models.portfolio import Holding


def test_portfolio_summary_and_hhi():
    holdings = [
        Holding(
            symbol="INFY",
            sector="IT",
            quantity=10,
            average_price=100.0,
            current_price=120.0,
            day_change_percent=1.0,
        ),
        Holding(
            symbol="TCS",
            sector="IT",
            quantity=10,
            average_price=100.0,
            current_price=80.0,
            day_change_percent=-1.0,
        ),
    ]

    result = analyze_portfolio(holdings)

    assert result["summary"]["invested_value"] == 2000.0
    assert result["summary"]["market_value"] == 2000.0
    assert result["summary"]["pnl"] == 0.0
    assert result["summary"]["pnl_percent"] == 0.0
    assert result["summary"]["holding_count"] == 2
    assert result["summary"]["hhi"] == 0.52

    assert result["holdings"][0]["pnl"] == 200.0
    assert result["holdings"][1]["pnl"] == -200.0


def test_historical_portfolio_values():
    holdings = [
        {"symbol": "INFY", "quantity": 10},
        {"symbol": "TCS", "quantity": 5},
    ]

    historical_prices = {
        "INFY": [
            {"date": "2026-01-01", "close": 100},
            {"date": "2026-01-02", "close": 110},
        ],
        "TCS": [
            {"date": "2026-01-01", "close": 200},
            {"date": "2026-01-02", "close": 220},
        ],
    }

    result = calculate_portfolio_historical_values(
        holdings,
        historical_prices,
    )

    assert result == [
        {"date": "2026-01-01", "portfolio_value": 2000.0},
        {"date": "2026-01-02", "portfolio_value": 2200.0},
    ]


def test_historical_portfolio_returns():
    portfolio_values = [
        {"date": "2026-01-01", "portfolio_value": 2000.0},
        {"date": "2026-01-02", "portfolio_value": 2200.0},
    ]

    result = calculate_portfolio_historical_returns(
        portfolio_values
    )

    assert len(result) == 1
    assert result[0]["date"] == "2026-01-02"
    assert result[0]["portfolio_value"] == 2200.0
    assert result[0]["previous_portfolio_value"] == 2000.0
    assert result[0]["return"] == 0.1
    assert result[0]["return_percent"] == 10.0


def test_contribution_analysis():
    holdings = [
        {
            "symbol": "INFY",
            "quantity": 10,
            "average_price": 100,
            "current_price": 120,
        },
        {
            "symbol": "TCS",
            "quantity": 10,
            "average_price": 100,
            "current_price": 110,
        },
    ]

    result = calculate_contribution_analysis(holdings)

    assert len(result) == 2

    assert result[0]["symbol"] == "INFY"
    assert result[0]["pnl"] == 200
    assert result[0]["contribution_percent"] == pytest.approx(
        66.6666666667
    )

    assert result[1]["symbol"] == "TCS"
    assert result[1]["pnl"] == 100
    assert result[1]["contribution_percent"] == pytest.approx(
        33.3333333333
    )
