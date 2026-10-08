from app.models.portfolio import Holding
from app.tools.portfolio_tools import (
    calculate_portfolio_metrics,
    get_portfolio,
)


def make_holdings():
    return [
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
            quantity=5,
            average_price=200.0,
            current_price=220.0,
            day_change_percent=0.5,
        ),
    ]


def test_get_portfolio():
    holdings = make_holdings()

    result = get_portfolio(
        user="test-user",
        holdings=holdings,
    )

    assert result.tool == "get_portfolio"
    assert result.status == "success"
    assert result.data["count"] == 2
    assert len(result.data["holdings"]) == 2

    assert result.data["holdings"][0]["symbol"] == "INFY"
    assert result.data["holdings"][1]["symbol"] == "TCS"


def test_calculate_portfolio_metrics():
    holdings = make_holdings()

    result = calculate_portfolio_metrics(
        user="test-user",
        holdings=holdings,
    )

    assert result.tool == "calculate_portfolio_metrics"
    assert result.status == "success"

    summary = result.data["summary"]

    assert summary["invested_value"] == 2000.0
    assert summary["market_value"] == 2300.0
    assert summary["pnl"] == 300.0
    assert summary["pnl_percent"] == 15.0
    assert summary["holding_count"] == 2
    assert "hhi" in summary

    assert len(result.data["holdings"]) == 2
