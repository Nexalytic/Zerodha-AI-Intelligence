from __future__ import annotations

import re

from fastapi import HTTPException

from app.demo_store import load_watchlist, save_watchlist


def get_watchlist(user: str) -> list[str]:
    return load_watchlist(user)


def save_user_watchlist(_user: str, symbols: list[str]) -> None:
    normalized = list(
        dict.fromkeys(
            symbol.strip().upper()
            for symbol in symbols
            if symbol.strip()
        )
    )

    if any(
        not re.fullmatch(r"[A-Z0-9.&_-]{1,24}", symbol)
        for symbol in normalized
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "Watchlist symbols must be 1–24 letters, numbers or "
                ". & _ - characters."
            ),
        )

    save_watchlist(_user, normalized)
