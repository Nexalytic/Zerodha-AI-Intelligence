from app.models.recommendation import Recommendation
from app.validation.recommendation_validator import (
    validate_recommendation_structure,
    validate_recommendation_numbers,
    validate_recommendation,
)


def concentration_recommendation(
    weight=0.60,
    hhi=0.40,
    source_required=False,
    source=None,
):
    evidence = {
        "weight": weight,
        "hhi": hhi,
    }

    if source_required:
        evidence["source_required"] = True

    if source is not None:
        evidence["source"] = source

    return Recommendation(
        type="CONCENTRATION_RISK",
        severity="CRITICAL",
        symbol="INFY",
        evidence=evidence,
        reason="INFY has a high portfolio concentration.",
        action="REDUCE",
        confidence=0.90,
    )


def loss_recommendation(pnl_percent=-35.0):
    return Recommendation(
        type="LOSS_RISK",
        severity="HIGH",
        symbol="INFY",
        evidence={
            "pnl_percent": pnl_percent,
        },
        reason="INFY has a significant loss.",
        action="REDUCE",
        confidence=0.90,
    )


def concentration_analytics():
    return {
        "holdings": [
            {
                "symbol": "INFY",
                "market_value": 6000.0,
            },
            {
                "symbol": "TCS",
                "market_value": 4000.0,
            },
        ],
        "summary": {
            "market_value": 10000.0,
            "hhi": 0.40,
        },
    }


def loss_analytics():
    return {
        "holdings": [
            {
                "symbol": "INFY",
                "average_price": 100.0,
                "current_price": 65.0,
            }
        ],
        "summary": {},
    }


def test_structure_validation_passes():
    recommendation = concentration_recommendation()

    result = validate_recommendation_structure(recommendation)

    assert result.status == "PASS"
    assert result.errors == []
    assert result.modified is False


def test_structure_validation_rejects_missing_evidence():
    recommendation = concentration_recommendation()
    recommendation.evidence = {}

    result = validate_recommendation_structure(recommendation)

    assert result.status == "REJECT"
    assert "Recommendation evidence is required." in result.errors


def test_structure_validation_rejects_missing_external_source():
    recommendation = concentration_recommendation(
        source_required=True,
    )

    result = validate_recommendation_structure(recommendation)

    assert result.status == "REJECT"
    assert (
        "An external source is required but was not provided."
        in result.errors
    )


def test_structure_validation_accepts_external_source():
    recommendation = concentration_recommendation(
        source_required=True,
        source="Alpha Vantage",
    )

    result = validate_recommendation_structure(recommendation)

    assert result.status == "PASS"
    assert result.errors == []


def test_concentration_numbers_pass():
    recommendation = concentration_recommendation(
        weight=0.60,
        hhi=0.40,
    )

    result = validate_recommendation_numbers(
        recommendation,
        concentration_analytics(),
    )

    assert result.status == "PASS"
    assert result.errors == []


def test_concentration_numbers_reject_wrong_weight():
    recommendation = concentration_recommendation(
        weight=0.50,
        hhi=0.40,
    )

    result = validate_recommendation_numbers(
        recommendation,
        concentration_analytics(),
    )

    assert result.status == "REJECT"
    assert (
        "Recommendation weight does not match portfolio analytics."
        in result.errors
    )


def test_concentration_numbers_reject_wrong_hhi():
    recommendation = concentration_recommendation(
        weight=0.60,
        hhi=0.30,
    )

    result = validate_recommendation_numbers(
        recommendation,
        concentration_analytics(),
    )

    assert result.status == "REJECT"
    assert (
        "Recommendation HHI does not match portfolio analytics."
        in result.errors
    )


def test_loss_numbers_pass():
    recommendation = loss_recommendation(-35.0)

    result = validate_recommendation_numbers(
        recommendation,
        loss_analytics(),
    )

    assert result.status == "PASS"
    assert result.errors == []


def test_loss_numbers_reject_wrong_pnl():
    recommendation = loss_recommendation(-20.0)

    result = validate_recommendation_numbers(
        recommendation,
        loss_analytics(),
    )

    assert result.status == "REJECT"
    assert (
        "Recommendation P&L percentage does not match "
        "portfolio analytics."
        in result.errors
    )


def test_full_validation_passes():
    recommendation = concentration_recommendation(
        weight=0.60,
        hhi=0.40,
    )

    result = validate_recommendation(
        recommendation,
        concentration_analytics(),
    )

    assert result.status == "PASS"
    assert result.errors == []
    assert result.modified is False


def test_full_validation_rejects_invalid_numbers():
    recommendation = concentration_recommendation(
        weight=0.50,
        hhi=0.40,
    )

    result = validate_recommendation(
        recommendation,
        concentration_analytics(),
    )

    assert result.status == "REJECT"
    assert result.errors
