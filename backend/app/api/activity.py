from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.demo_store import require_user


router = APIRouter(prefix="/api/v1/activity", tags=["activity"])


DB_PATH = Path(__file__).resolve().parents[2] / "zerodha-demo.db"


def _db() -> sqlite3.Connection:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def _json_or_none(value: str | None) -> Any:
    if not value:
        return None

    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return value


@router.get("")
def get_activity(
    user: str = Depends(require_user),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    with _db() as db:
        runs = db.execute(
            """
            SELECT
                id,
                question,
                status,
                mode,
                error,
                started_at,
                completed_at
            FROM analysis_runs
            WHERE demo_user = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user, limit),
        ).fetchall()

        result: list[dict[str, Any]] = []

        for run in runs:
            run_id = run["id"]

            events = db.execute(
                """
                SELECT
                    id,
                    event_type,
                    message,
                    details_json,
                    created_at
                FROM audit_events
                WHERE run_id = ?
                ORDER BY id ASC
                """,
                (run_id,),
            ).fetchall()

            tool_calls = db.execute(
                """
                SELECT
                    id,
                    tool_name,
                    status,
                    input_json,
                    output_json,
                    started_at,
                    completed_at
                FROM tool_calls
                WHERE run_id = ?
                ORDER BY id ASC
                """,
                (run_id,),
            ).fetchall()

            recommendations = db.execute(
                """
                SELECT
                    id,
                    recommendation_type,
                    severity,
                    symbol,
                    action,
                    confidence,
                    reason,
                    evidence_json,
                    validation_status,
                    created_at
                FROM recommendations
                WHERE run_id = ?
                ORDER BY id ASC
                """,
                (run_id,),
            ).fetchall()

            result.append(
                {
                    "id": run_id,
                    "question": run["question"],
                    "status": run["status"],
                    "mode": run["mode"],
                    "error": run["error"],
                    "started_at": run["started_at"],
                    "completed_at": run["completed_at"],
                    "events": [
                        {
                            "id": event["id"],
                            "event_type": event["event_type"],
                            "message": event["message"],
                            "details": _json_or_none(event["details_json"]),
                            "created_at": event["created_at"],
                        }
                        for event in events
                    ],
                    "tool_calls": [
                        {
                            "id": call["id"],
                            "tool_name": call["tool_name"],
                            "status": call["status"],
                            "input": _json_or_none(call["input_json"]),
                            "output": _json_or_none(call["output_json"]),
                            "started_at": call["started_at"],
                            "completed_at": call["completed_at"],
                        }
                        for call in tool_calls
                    ],
                    "recommendations": [
                        {
                            "id": recommendation["id"],
                            "type": recommendation["recommendation_type"],
                            "severity": recommendation["severity"],
                            "symbol": recommendation["symbol"],
                            "action": recommendation["action"],
                            "confidence": recommendation["confidence"],
                            "reason": recommendation["reason"],
                            "evidence": _json_or_none(
                                recommendation["evidence_json"]
                            ),
                            "validation_status": recommendation[
                                "validation_status"
                            ],
                            "created_at": recommendation["created_at"],
                        }
                        for recommendation in recommendations
                    ],
                }
            )

    return {
        "count": len(result),
        "items": result,
    }