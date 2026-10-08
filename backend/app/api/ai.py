from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.demo_store import require_user
from app.models.analysis import AnalystRequest
from app.services.ai_service import answer_question

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


@router.post("/answer")
async def answer(
    payload: AnalystRequest,
    user: str = Depends(require_user),
) -> dict[str, Any]:
    return await answer_question(payload.question, payload.holdings)