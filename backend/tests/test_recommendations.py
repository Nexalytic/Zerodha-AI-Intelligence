from app.models.portfolio import Holding
from app.recommendations.rule_engine import (
    concentration_recommendations,
    loss_recommendations,
)


def holding(
    symbol,
    quantity,
    average_price,
    current_price,
):
    return Holding(
        symbol=symbol,
        sector="IT",
        quantity=quantity,
        average_price=average_price,
        current_price=current_price,
        day_change_percent=0.0,
    )


def test_concentration_critical():
    holdings = [
        holding("INFY", 10, 100, 100),
        holding("TCS", 1, 100, 100),
    ]

    result = concentration_recommendations(holdings)

    assert len(result) == 1
    assert result[0].type == "CONCENTRATION_RISK"
    assert result[0].severity == "CRITICAL"
    assert result[0].symbol == "INFY"
    assert result[0].action == "REDUCE"
    assert result[0].evidence["weight"] > 0.50


def test_concentration_high():
    holdings = [
        holding("INFY", 45, 100, 100),
        holding("TCS", 30, 100, 100),
        holding("HDFC", 25, 100, 100),
    ]

    result = concentration_recommendations(holdings)

    assert len(result) == 3

    infy = next(
        recommendation
        for recommendation in result
        if recommendation.symbol == "INFY"
    )

    assert infy.severity == "HIGH"
    assert infy.action == "REVIEW"
    assert infy.evidence["weight"] == 0.45


def test_concentration_medium():
    holdings = [
        holding("INFY", 30, 100, 100),
        holding("TCS", 30, 100, 100),
        holding("HDFC", 20, 100, 100),
        holding("ITC", 20, 100, 100),
    ]

    result = concentration_recommendations(holdings)

    assert len(result) == 2

    assert all(
        recommendation.severity == "MEDIUM"
        for recommendation in result
    )

    assert all(
        recommendation.action == "REVIEW"
        for recommendation in result
    )


def test_concentration_below_threshold():
    holdings = [
        holding("INFY", 2, 100, 100),
        holding("TCS", 2, 100, 100),
        holding("HDFC", 2, 100, 100),
        holding("ITC", 2, 100, 100),
        holding("SBIN", 2, 100, 100),
    ]

    result = concentration_recommendations(holdings)

    assert result == []


def test_loss_high():
    holdings = [
        holding("INFY", 10, 100, 65),
    ]

    result = loss_recommendations(holdings)

    assert len(result) == 1
    assert result[0].type == "LOSS_RISK"
    assert result[0].severity == "HIGH"
    assert result[0].symbol == "INFY"
    assert result[0].action == "REDUCE"
    assert result[0].evidence["pnl_percent"] == -35.0


def test_loss_medium():
    holdings = [
        holding("INFY", 10, 100, 80),
    ]

    result = loss_recommendations(holdings)

    assert len(result) == 1
    assert result[0].severity == "MEDIUM"
    assert result[0].action == "REVIEW"
    assert result[0].evidence["pnl_percent"] == -20.0


def test_loss_below_threshold():
    holdings = [
        holding("INFY", 10, 100, 90),
    ]

    result = loss_recommendations(holdings)

    assert result == []


def test_empty_holdings():
    assert concentration_recommendations([]) == []
    assert loss_recommendations([]) == []
