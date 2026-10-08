from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class Recommendation(BaseModel):
    type: str = Field(min_length=1, max_length=80)
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    symbol: str | None = Field(default=None, max_length=24)
    evidence: dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(min_length=1, max_length=500)
    action: Literal["REVIEW", "MONITOR", "HOLD", "REDUCE", "DIVERSIFY"]
    confidence: float = Field(ge=0.0, le=1.0)
