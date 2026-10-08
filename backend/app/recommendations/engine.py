from __future__ import annotations

from app.models.portfolio import Holding
from app.models.recommendation import Recommendation
from app.recommendations.rule_engine import (
    concentration_recommendations,
    loss_recommendations,
)


def generate_recommendations(
    holdings: list[Holding],
) -> list[Recommendation]:
    recommendations: list[Recommendation] = []

    recommendations.extend(
        concentration_recommendations(holdings)
    )

    recommendations.extend(
        loss_recommendations(holdings)
    )

    return recommendations
