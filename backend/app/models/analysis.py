from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.portfolio import Holding


class AnalyzeRequest(BaseModel):
    holdings: list[Holding] = Field(min_length=1, max_length=1000)


class AnalystRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1200)
    holdings: list[Holding] = Field(default_factory=list, max_length=1000)