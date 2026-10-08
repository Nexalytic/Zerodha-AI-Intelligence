from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, UploadFile, File

from app.demo_store import load_portfolio, require_user, save_portfolio
from app.models.analysis import AnalyzeRequest
from app.models.portfolio import PortfolioSaveRequest
from app.services.csv_service import preview_csv as preview_csv_service
from app.services.portfolio_service import analyze_portfolio

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


@router.post("/analyze")
def analyze(
    payload: AnalyzeRequest,
    user: str = Depends(require_user),
) -> dict[str, Any]:
    return analyze_portfolio(payload.holdings)


@router.get("/holdings")
def get_portfolio_holdings(
    user: str = Depends(require_user),
) -> dict[str, Any]:
    return {
        "holdings": load_portfolio(user),
        "source": "local demo portfolio; uploaded prices or Alpha Vantage quote updates",
    }


@router.put("/holdings")
def put_portfolio_holdings(
    payload: PortfolioSaveRequest,
    user: str = Depends(require_user),
) -> dict[str, Any]:
    rows = [holding.model_dump() for holding in payload.holdings]
    save_portfolio(user, rows)
    return {
        "holdings": rows,
        "count": len(rows),
        "message": "Portfolio saved to your account.",
    }


@router.post("/preview-csv")
async def preview_csv(
    file: UploadFile = File(...),
    user: str = Depends(require_user),
) -> dict[str, Any]:
    return await preview_csv_service(file)
