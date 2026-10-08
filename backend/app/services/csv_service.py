from __future__ import annotations

import csv
import io
from typing import Any

from fastapi import HTTPException, UploadFile

from app.models.portfolio import Holding


async def preview_csv(file: UploadFile) -> dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Upload a CSV file")

    raw = await file.read(5_000_001)

    if len(raw) > 5_000_000:
        raise HTTPException(status_code=413, detail="CSV exceeds 5 MB")

    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))

        if not reader.fieldnames:
            raise ValueError("CSV has no header row")

        aliases = {
            "symbol": ("symbol", "ticker", "stock"),
            "quantity": ("quantity", "qty", "shares"),
            "average_price": (
                "average price",
                "avg price",
                "avg_price",
                "average_price",
                "buy price",
            ),
            "current_price": (
                "current price",
                "ltp",
                "market price",
                "price",
            ),
            "sector": ("sector",),
        }

        mapping = {
            target: next(
                (
                    col
                    for col in reader.fieldnames
                    if any(alias in col.lower().strip() for alias in names)
                ),
                None,
            )
            for target, names in aliases.items()
        }

        missing = [
            key
            for key in ("symbol", "quantity", "average_price", "current_price")
            if not mapping[key]
        ]

        if missing:
            raise ValueError(
                "Could not identify required columns: " + ", ".join(missing)
            )

        rows: list[Holding] = []

        for source in reader:
            try:
                rows.append(
                    Holding(
                        symbol=str(source[mapping["symbol"]]).strip(),
                        quantity=float(
                            str(source[mapping["quantity"]]).replace(",", "")
                        ),
                        average_price=float(
                            str(source[mapping["average_price"]])
                            .replace(",", "")
                            .replace("₹", "")
                        ),
                        current_price=float(
                            str(source[mapping["current_price"]])
                            .replace(",", "")
                            .replace("₹", "")
                        ),
                        sector=str(
                            source.get(mapping["sector"], "Unclassified")
                            or "Unclassified"
                        ).strip(),
                    )
                )
            except (ValueError, TypeError):
                continue

        if not rows:
            raise ValueError("No valid holding rows found")

        return {
            "holdings": [holding.model_dump() for holding in rows],
            "count": len(rows),
            "column_mapping": mapping,
            "requires_user_confirmation": True,
            "warnings": [
                "Review all extracted quantities and prices before analysis."
            ],
        }

    except (UnicodeDecodeError, csv.Error, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
