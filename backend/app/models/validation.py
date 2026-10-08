from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    status: Literal["PASS", "REJECT", "MODIFY"]
    recommendation_type: str
    symbol: str | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    modified: bool = False