from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.demo_store import require_user
from app.models.portfolio import WatchlistSaveRequest
from app.services.watchlist_service import (
    get_watchlist as get_watchlist_service,
    save_user_watchlist,
)

router = APIRouter(prefix="/api/v1/watchlist", tags=["watchlist"])


@router.get("")
def get_watchlist(
    user: str = Depends(require_user),
) -> dict[str, Any]:
    return {"symbols": get_watchlist_service(user)}


@router.put("")
def put_watchlist(
    payload: WatchlistSaveRequest,
    user: str = Depends(require_user),
) -> dict[str, Any]:
    save_user_watchlist(user, payload.symbols)
    return {"symbols": get_watchlist_service(user)}