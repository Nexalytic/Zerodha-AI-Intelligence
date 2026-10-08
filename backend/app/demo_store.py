"""Single-user SQLite storage for the local demonstration app."""
from __future__ import annotations
import json
import os
import sqlite3
import time
from pathlib import Path

def _path() -> str:
    url=os.getenv("DATABASE_URL", "sqlite:///./zerodha-demo.db")
    return url.removeprefix("sqlite:///") if url.startswith("sqlite:///") else url

def _db():
    db=sqlite3.connect(_path(), timeout=10)
    db.row_factory=sqlite3.Row
    return db

def _init() -> None:
    Path(_path()).parent.mkdir(parents=True, exist_ok=True)

    with _db() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS portfolio_holdings (
                demo_user TEXT PRIMARY KEY,
                holdings_json TEXT NOT NULL,
                updated_at REAL NOT NULL
            )
            """
        )

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS watchlists (
                demo_user TEXT PRIMARY KEY,
                symbols_json TEXT NOT NULL,
                updated_at REAL NOT NULL
            )
            """
        )

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS market_quote_cache (
                symbol TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                retrieved_at REAL NOT NULL
            )
            """
        )

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS alpha_vantage_usage (
                usage_day TEXT PRIMARY KEY,
                request_count INTEGER NOT NULL,
                last_request_at REAL NOT NULL
            )
            """
        )

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS market_prices (
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL NOT NULL,
                source TEXT NOT NULL,
                fetched_at REAL NOT NULL,
                PRIMARY KEY (symbol, date)
            )
            """
        )

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                timestamp REAL NOT NULL,
                portfolio_value REAL NOT NULL,
                invested_value REAL NOT NULL,
                pnl REAL NOT NULL
            )
            """
        )

        # Phase 10: one record for each important analysis execution.
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                demo_user TEXT NOT NULL,
                question TEXT NOT NULL,
                status TEXT NOT NULL,
                mode TEXT,
                started_at REAL NOT NULL,
                completed_at REAL,
                error TEXT
            )
            """
        )

        # Phase 10: human-readable events that explain what happened.
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                details_json TEXT,
                created_at REAL NOT NULL,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(id)
            )
            """
        )

        # Phase 10: exact tools used during an analysis.
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS tool_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                tool_name TEXT NOT NULL,
                status TEXT NOT NULL,
                input_json TEXT,
                output_json TEXT,
                started_at REAL NOT NULL,
                completed_at REAL,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(id)
            )
            """
        )

        # Phase 10: recommendations produced during an analysis.
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                recommendation_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                symbol TEXT,
                action TEXT NOT NULL,
                confidence REAL NOT NULL,
                reason TEXT NOT NULL,
                evidence_json TEXT NOT NULL,
                validation_status TEXT,
                created_at REAL NOT NULL,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(id)
            )
            """
        )
                # Phase 11: HTTP request telemetry.
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS api_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method TEXT NOT NULL,
                path TEXT NOT NULL,
                status_code INTEGER NOT NULL,
                duration_ms REAL NOT NULL,
                error TEXT,
                created_at REAL NOT NULL
            )
            """
        )
_init()

def load_portfolio(_user: str) -> list[dict]:
    with _db() as db:
        row=db.execute("SELECT holdings_json FROM portfolio_holdings WHERE demo_user = 'local' ").fetchone()
    return json.loads(row["holdings_json"]) if row else []

def save_portfolio(_user: str, holdings: list[dict]) -> None:
    with _db() as db:
        db.execute("INSERT INTO portfolio_holdings(demo_user,holdings_json,updated_at) VALUES('local',?,?) ON CONFLICT(demo_user) DO UPDATE SET holdings_json=excluded.holdings_json,updated_at=excluded.updated_at", (json.dumps(holdings,separators=(",",":")),time.time()))

def load_watchlist(_user: str) -> list[str]:
    with _db() as db:
        row=db.execute("SELECT symbols_json FROM watchlists WHERE demo_user = 'local'").fetchone()
    return json.loads(row["symbols_json"]) if row else []

def save_watchlist(_user: str, symbols: list[str]) -> None:
    with _db() as db:
        db.execute("INSERT INTO watchlists(demo_user,symbols_json,updated_at) VALUES('local',?,?) ON CONFLICT(demo_user) DO UPDATE SET symbols_json=excluded.symbols_json,updated_at=excluded.updated_at", (json.dumps(symbols,separators=(",",":")),time.time()))

def require_user() -> str:
    return "local-demo-user"


def load_quote(symbol: str, max_age: int) -> dict | None:
    with _db() as db:
        row=db.execute("SELECT payload_json,retrieved_at FROM market_quote_cache WHERE symbol=?",(symbol,)).fetchone()
    if not row or time.time()-row["retrieved_at"]>max_age: return None
    quote=json.loads(row["payload_json"]); quote["retrieved_at"]=row["retrieved_at"]; quote["cached"]=True
    return quote

def save_quote(symbol: str, quote: dict) -> None:
    with _db() as db:
        db.execute("INSERT INTO market_quote_cache(symbol,payload_json,retrieved_at) VALUES(?,?,?) ON CONFLICT(symbol) DO UPDATE SET payload_json=excluded.payload_json,retrieved_at=excluded.retrieved_at",(symbol,json.dumps(quote,separators=(",",":")),time.time()))

def alpha_usage(day: str) -> tuple[int,float]:
    with _db() as db:
        row=db.execute("SELECT request_count,last_request_at FROM alpha_vantage_usage WHERE usage_day=?",(day,)).fetchone()
    return (row["request_count"],row["last_request_at"]) if row else (0,0.0)

def record_alpha_request(day: str, now: float) -> None:
    with _db() as db:
        db.execute("INSERT INTO alpha_vantage_usage(usage_day,request_count,last_request_at) VALUES(?,1,?) ON CONFLICT(usage_day) DO UPDATE SET request_count=alpha_vantage_usage.request_count+1,last_request_at=excluded.last_request_at",(day,now))
def save_market_prices(rows: list[dict]) -> None:
    with _db() as db:
        db.executemany(
            """
            INSERT INTO market_prices
            (symbol, date, open, high, low, close, volume, source, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, date) DO UPDATE SET
                open=excluded.open,
                high=excluded.high,
                low=excluded.low,
                close=excluded.close,
                volume=excluded.volume,
                source=excluded.source,
                fetched_at=excluded.fetched_at
            """,
            [
                (
                    row["symbol"],
                    row["date"],
                    row["open"],
                    row["high"],
                    row["low"],
                    row["close"],
                    row["volume"],
                    row["source"],
                    row["fetched_at"],
                )
                for row in rows
            ],
        )


def load_market_prices(symbol: str, limit: int = 100) -> list[dict]:
    with _db() as db:
        rows = db.execute(
            """
            SELECT symbol, date, open, high, low, close,
                   volume, source, fetched_at
            FROM market_prices
            WHERE symbol = ?
            ORDER BY date DESC
            LIMIT ?
            """,
            (symbol.upper(), limit),
        ).fetchall()

    return [dict(row) for row in rows]
def save_portfolio_snapshot(
    portfolio_value: float,
    invested_value: float,
    timestamp: float | None = None,
) -> None:
    snapshot_time = timestamp if timestamp is not None else time.time()
    pnl = portfolio_value - invested_value

    with _db() as db:
        db.execute(
            """
            INSERT INTO portfolio_snapshots
            (timestamp, portfolio_value, invested_value, pnl)
            VALUES (?, ?, ?, ?)
            """,
            (
                snapshot_time,
                portfolio_value,
                invested_value,
                pnl,
            ),
        )


def load_portfolio_snapshots(limit: int = 100) -> list[dict]:
    with _db() as db:
        rows = db.execute(
            """
            SELECT timestamp, portfolio_value, invested_value, pnl
            FROM portfolio_snapshots
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]
# ---------------------------------------------------------------------------
# Phase 10: Analysis audit trail
# ---------------------------------------------------------------------------

def create_analysis_run(
    user: str,
    question: str,
) -> int:
    started_at = time.time()

    with _db() as db:
        cursor = db.execute(
            """
            INSERT INTO analysis_runs
            (demo_user, question, status, started_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                user,
                question,
                "RUNNING",
                started_at,
            ),
        )
        return int(cursor.lastrowid)


def complete_analysis_run(
    run_id: int,
    status: str = "COMPLETED",
    mode: str | None = None,
    error: str | None = None,
) -> None:
    completed_at = time.time()

    with _db() as db:
        db.execute(
            """
            UPDATE analysis_runs
            SET status = ?,
                mode = ?,
                completed_at = ?,
                error = ?
            WHERE id = ?
            """,
            (
                status,
                mode,
                completed_at,
                error,
                run_id,
            ),
        )


def record_audit_event(
    run_id: int,
    event_type: str,
    message: str,
    details: dict | None = None,
) -> int:
    created_at = time.time()

    details_json = (
        json.dumps(details, separators=(",", ":"))
        if details is not None
        else None
    )

    with _db() as db:
        cursor = db.execute(
            """
            INSERT INTO audit_events
            (run_id, event_type, message, details_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                run_id,
                event_type,
                message,
                details_json,
                created_at,
            ),
        )
        return int(cursor.lastrowid)


def record_tool_call(
    run_id: int,
    tool_name: str,
    status: str,
    input_data: dict | None = None,
    output_data: dict | None = None,
    started_at: float | None = None,
    completed_at: float | None = None,
) -> int:
    tool_started_at = (
        started_at if started_at is not None else time.time()
    )

    input_json = (
        json.dumps(input_data, separators=(",", ":"))
        if input_data is not None
        else None
    )

    output_json = (
        json.dumps(output_data, separators=(",", ":"))
        if output_data is not None
        else None
    )

    with _db() as db:
        cursor = db.execute(
            """
            INSERT INTO tool_calls
            (
                run_id,
                tool_name,
                status,
                input_json,
                output_json,
                started_at,
                completed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                tool_name,
                status,
                input_json,
                output_json,
                tool_started_at,
                completed_at,
            ),
        )
        return int(cursor.lastrowid)


def record_recommendation(
    run_id: int,
    recommendation: dict,
    validation_status: str,
) -> int:
    created_at = time.time()

    with _db() as db:
        cursor = db.execute(
            """
            INSERT INTO recommendations
            (
                run_id,
                recommendation_type,
                severity,
                symbol,
                action,
                confidence,
                reason,
                evidence_json,
                validation_status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                recommendation["type"],
                recommendation["severity"],
                recommendation.get("symbol"),
                recommendation["action"],
                recommendation["confidence"],
                recommendation["reason"],
                json.dumps(
                    recommendation.get("evidence", {}),
                    separators=(",", ":"),
                ),
                validation_status,
                created_at,
            ),
        )
        return int(cursor.lastrowid)
def record_api_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    error: str | None = None,
) -> int:
    created_at = time.time()

    with _db() as db:
        cursor = db.execute(
            """
            INSERT INTO api_requests
            (method, path, status_code, duration_ms, error, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                method,
                path,
                status_code,
                duration_ms,
                error,
                created_at,
            ),
        )

        return int(cursor.lastrowid)
def get_operations_metrics() -> dict:
    with _db() as db:
        api_row = db.execute(
            """
            SELECT
                COUNT(*) AS request_count,
                COALESCE(
                    AVG(duration_ms),
                    0
                ) AS average_latency_ms,
                COALESCE(
                    SUM(
                        CASE
                            WHEN status_code >= 400 THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS error_count,
                COALESCE(
                    SUM(
                        CASE
                            WHEN status_code < 400 THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS success_count
            FROM api_requests
            """
        ).fetchone()

        tool_row = db.execute(
            """
            SELECT
                COUNT(*) AS tool_call_count,
                COALESCE(
                    SUM(
                        CASE
                            WHEN status = 'SUCCESS' THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS tool_success_count,
                COALESCE(
                    AVG(
                        CASE
                            WHEN completed_at IS NOT NULL
                            THEN (completed_at - started_at) * 1000
                        END
                    ),
                    0
                ) AS average_latency_ms
            FROM tool_calls
            """
        ).fetchone()

        ai_row = db.execute(
            """
            SELECT
                COUNT(*) AS ai_request_count,
                COALESCE(
                    SUM(
                        CASE
                            WHEN status = 'COMPLETED' THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS ai_success_count,
                COALESCE(
                    SUM(
                        CASE
                            WHEN status = 'FAILED' THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS ai_error_count
            FROM analysis_runs
            """
        ).fetchone()

        alpha_row = db.execute(
            """
            SELECT
                COALESCE(SUM(request_count), 0) AS requests_used
            FROM alpha_vantage_usage
            WHERE usage_day = date('now', 'localtime')
            """
        ).fetchone()

        api_requests = int(api_row["request_count"] or 0)
        api_successes = int(api_row["success_count"] or 0)
        api_errors = int(api_row["error_count"] or 0)

        tool_calls = int(tool_row["tool_call_count"] or 0)
        tool_successes = int(tool_row["tool_success_count"] or 0)

        ai_requests = int(ai_row["ai_request_count"] or 0)
        ai_successes = int(ai_row["ai_success_count"] or 0)
        ai_errors = int(ai_row["ai_error_count"] or 0)

        return {
            "api_requests": api_requests,
            "api_success_rate": (
                round((api_successes / api_requests) * 100, 2)
                if api_requests
                else 100.0
            ),
            "api_average_latency_ms": round(
                float(api_row["average_latency_ms"] or 0),
                2,
            ),
            "api_errors": api_errors,
            "ai_requests": ai_requests,
            "ai_success_rate": (
                round((ai_successes / ai_requests) * 100, 2)
                if ai_requests
                else 100.0
            ),
            "ai_errors": ai_errors,
            "tool_calls": tool_calls,
            "tool_success_rate": (
                round((tool_successes / tool_calls) * 100, 2)
                if tool_calls
                else 100.0
            ),
            "tool_average_latency_ms": round(
                float(tool_row["average_latency_ms"] or 0),
                2,
            ),
            "alpha_vantage_requests_used": int(
                alpha_row["requests_used"] or 0
            ),
            "alpha_vantage_daily_limit": int(
                os.getenv("ALPHA_VANTAGE_DAILY_LIMIT", "25")
            ),
        }