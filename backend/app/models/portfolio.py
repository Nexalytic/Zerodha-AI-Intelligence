from __future__ import annotations

from pydantic import BaseModel, Field


class Holding(BaseModel):
    symbol: str = Field(min_length=1, max_length=24)
    quantity: float = Field(gt=0)
    average_price: float = Field(gt=0)
    current_price: float = Field(gt=0)
    sector: str = "Unclassified"
    # Optional display fields. These are preserved from the original backend
    # so portfolio display data is not silently dropped when saving.
    name: str | None = Field(default=None, max_length=80)
    day_change_percent: float = Field(default=0.0, ge=-100, le=1000)


class PortfolioSaveRequest(BaseModel):
    holdings: list[Holding] = Field(max_length=1000)


class WatchlistSaveRequest(BaseModel):
    symbols: list[str] = Field(max_length=200)