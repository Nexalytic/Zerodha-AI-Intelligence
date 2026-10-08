from __future__ import annotations

from app.models.portfolio import Holding
from app.models.recommendation import Recommendation


def concentration_recommendations(
    holdings: list[Holding],
) -> list[Recommendation]:
    if not holdings:
        return []

    total_market_value = sum(
        holding.quantity * holding.current_price
        for holding in holdings
    )

    if total_market_value <= 0:
        return []

    hhi = sum(
        (
            (
                holding.quantity * holding.current_price
            ) / total_market_value
        ) ** 2
        for holding in holdings
    )

    recommendations: list[Recommendation] = []

    for holding in holdings:
        market_value = holding.quantity * holding.current_price
        weight = market_value / total_market_value

        if weight >= 0.50:
            severity = "CRITICAL"
            action = "REDUCE"
            confidence = min(1.0, 0.80 + weight * 0.20)
        elif weight >= 0.40:
            severity = "HIGH"
            action = "REVIEW"
            confidence = min(1.0, 0.75 + weight * 0.20)
        elif weight >= 0.25:
            severity = "MEDIUM"
            action = "REVIEW"
            confidence = min(1.0, 0.70 + weight * 0.20)
        else:
            continue

        recommendations.append(
            Recommendation(
                type="CONCENTRATION_RISK",
                severity=severity,
                symbol=holding.symbol,
                evidence={
                    "weight": round(weight, 4),
                    "weight_percent": round(weight * 100, 2),
                    "hhi": round(hhi, 4),
                    "holding_count": len(holdings),
                },
                reason="Large single-position exposure increases concentration risk.",
                action=action,
                confidence=round(confidence, 2),
            )
        )

    return recommendations


def loss_recommendations(
    holdings: list[Holding],
) -> list[Recommendation]:
    recommendations: list[Recommendation] = []

    for holding in holdings:
        pnl_percent = (
            (
                holding.current_price - holding.average_price
            )
            / holding.average_price
            * 100
        )

        if pnl_percent <= -30:
            severity = "HIGH"
            action = "REDUCE"
            confidence = 0.90
        elif pnl_percent <= -15:
            severity = "MEDIUM"
            action = "REVIEW"
            confidence = 0.80
        else:
            continue

        recommendations.append(
            Recommendation(
                type="LOSS_RISK",
                severity=severity,
                symbol=holding.symbol,
                evidence={
                    "pnl_percent": round(pnl_percent, 2),
                    "average_price": round(holding.average_price, 2),
                    "current_price": round(holding.current_price, 2),
                },
                reason="The position has experienced a significant loss relative to its average purchase price.",
                action=action,
                confidence=confidence,
            )
        )

    return recommendations
