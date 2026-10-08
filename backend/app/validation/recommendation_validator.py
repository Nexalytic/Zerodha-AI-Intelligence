from __future__ import annotations

from typing import Any

from app.models.recommendation import Recommendation
from app.models.validation import ValidationResult


WEIGHT_TOLERANCE = 0.0001
HHI_TOLERANCE = 0.0001
PERCENT_TOLERANCE = 0.01


def validate_recommendation_structure(
    recommendation: Recommendation,
) -> ValidationResult:
    """
    Validate the structural and source requirements of a recommendation.

    This function does not recalculate financial values.
    Financial-number consistency is handled by
    validate_recommendation_numbers().
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not recommendation.type:
        errors.append("Recommendation type is required.")

    if not recommendation.reason:
        errors.append("Recommendation reason is required.")

    if not recommendation.action:
        errors.append("Recommendation action is required.")

    if not recommendation.evidence:
        errors.append("Recommendation evidence is required.")

    if recommendation.symbol is None:
        warnings.append("Recommendation has no symbol.")

    source_required = bool(
        recommendation.evidence.get("source_required", False)
    )

    if source_required:
        source = recommendation.evidence.get("source")

        if not source:
            errors.append(
                "An external source is required but was not provided."
            )

    status = "REJECT" if errors else "PASS"

    return ValidationResult(
        status=status,
        recommendation_type=recommendation.type,
        symbol=recommendation.symbol,
        errors=errors,
        warnings=warnings,
        modified=False,
    )


def validate_recommendation_numbers(
    recommendation: Recommendation,
    analytics: dict[str, Any],
) -> ValidationResult:
    """
    Validate that recommendation evidence matches deterministic
    portfolio analytics.

    Supported recommendation types:
    - CONCENTRATION_RISK
    - LOSS_RISK
    """
    errors: list[str] = []
    warnings: list[str] = []

    holdings = analytics.get("holdings", [])
    summary = analytics.get("summary", {})

    if recommendation.type == "CONCENTRATION_RISK":
        _validate_concentration_numbers(
            recommendation=recommendation,
            holdings=holdings,
            summary=summary,
            errors=errors,
        )

    elif recommendation.type == "LOSS_RISK":
        _validate_loss_numbers(
            recommendation=recommendation,
            holdings=holdings,
            errors=errors,
        )

    else:
        warnings.append(
            f"No financial-number validator is defined for "
            f"recommendation type '{recommendation.type}'."
        )

    status = "REJECT" if errors else "PASS"

    return ValidationResult(
        status=status,
        recommendation_type=recommendation.type,
        symbol=recommendation.symbol,
        errors=errors,
        warnings=warnings,
        modified=False,
    )


def _validate_concentration_numbers(
    recommendation: Recommendation,
    holdings: list[dict[str, Any]],
    summary: dict[str, Any],
    errors: list[str],
) -> None:
    """Validate concentration weight and HHI evidence."""

    if not recommendation.symbol:
        errors.append(
            "CONCENTRATION_RISK recommendation requires a symbol."
        )
        return

    matching_holding = next(
        (
            holding
            for holding in holdings
            if holding.get("symbol") == recommendation.symbol
        ),
        None,
    )

    if matching_holding is None:
        errors.append(
            "Recommendation symbol was not found in portfolio analytics."
        )
        return

    if "market_value" not in matching_holding:
        errors.append(
            "Portfolio analytics is missing market_value for "
            "the recommendation symbol."
        )
        return

    if "market_value" not in summary:
        errors.append(
            "Portfolio analytics is missing total market_value."
        )
        return

    if "weight" not in recommendation.evidence:
        errors.append(
            "Recommendation evidence is missing weight."
        )
    else:
        try:
            supplied_weight = float(
                recommendation.evidence["weight"]
            )
        except (TypeError, ValueError):
            errors.append(
                "Recommendation weight must be numeric."
            )
        else:
            market_value = float(
                matching_holding["market_value"]
            )
            total_market_value = float(
                summary["market_value"]
            )

            calculated_weight = (
                market_value / total_market_value
                if total_market_value
                else 0.0
            )

            if abs(
                calculated_weight - supplied_weight
            ) > WEIGHT_TOLERANCE:
                errors.append(
                    "Recommendation weight does not match "
                    "portfolio analytics."
                )

    if "hhi" not in recommendation.evidence:
        errors.append(
            "Recommendation evidence is missing hhi."
        )
    elif "hhi" not in summary:
        errors.append(
            "Portfolio analytics is missing hhi."
        )
    else:
        try:
            supplied_hhi = float(
                recommendation.evidence["hhi"]
            )
            calculated_hhi = float(
                summary["hhi"]
            )
        except (TypeError, ValueError):
            errors.append(
                "Recommendation HHI must be numeric."
            )
        else:
            if abs(
                calculated_hhi - supplied_hhi
            ) > HHI_TOLERANCE:
                errors.append(
                    "Recommendation HHI does not match "
                    "portfolio analytics."
                )


def _validate_loss_numbers(
    recommendation: Recommendation,
    holdings: list[dict[str, Any]],
    errors: list[str],
) -> None:
    """Validate LOSS_RISK P&L percentage evidence."""

    if not recommendation.symbol:
        errors.append(
            "LOSS_RISK recommendation requires a symbol."
        )
        return

    matching_holding = next(
        (
            holding
            for holding in holdings
            if holding.get("symbol") == recommendation.symbol
        ),
        None,
    )

    if matching_holding is None:
        errors.append(
            "Recommendation symbol was not found in portfolio analytics."
        )
        return

    required_fields = (
        "average_price",
        "current_price",
    )

    for field in required_fields:
        if field not in matching_holding:
            errors.append(
                f"Portfolio analytics is missing {field} "
                "for the recommendation symbol."
            )

    if errors:
        return

    if "pnl_percent" not in recommendation.evidence:
        errors.append(
            "Recommendation evidence is missing pnl_percent."
        )
        return

    try:
        average_price = float(
            matching_holding["average_price"]
        )
        current_price = float(
            matching_holding["current_price"]
        )
        supplied_pnl_percent = float(
            recommendation.evidence["pnl_percent"]
        )
    except (TypeError, ValueError):
        errors.append(
            "Recommendation P&L evidence must be numeric."
        )
        return

    calculated_pnl_percent = (
        (
            (current_price - average_price)
            / average_price
            * 100
        )
        if average_price
        else 0.0
    )

    if abs(
        calculated_pnl_percent - supplied_pnl_percent
    ) > PERCENT_TOLERANCE:
        errors.append(
            "Recommendation P&L percentage does not match "
            "portfolio analytics."
        )
def validate_recommendation(
    recommendation: Recommendation,
    analytics: dict[str, Any],
) -> ValidationResult:
    """
    Run all validation checks for a single recommendation.

    A recommendation passes only when both structural and
    financial-number validation pass.
    """

    structure_result = validate_recommendation_structure(
        recommendation
    )

    number_result = validate_recommendation_numbers(
        recommendation,
        analytics,
    )

    errors = (
        structure_result.errors
        + number_result.errors
    )

    warnings = (
        structure_result.warnings
        + number_result.warnings
    )

    if errors:
        status = "REJECT"
    else:
        status = "PASS"

    return ValidationResult(
        status=status,
        recommendation_type=recommendation.type,
        symbol=recommendation.symbol,
        errors=errors,
        warnings=warnings,
        modified=False,
    )
