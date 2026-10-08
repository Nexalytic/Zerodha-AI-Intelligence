from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "zerodha-ai-demo-api"
    assert "timestamp" in data


def test_portfolio_analyze_endpoint():
    payload = {
        "holdings": [
            {
                "symbol": "INFY",
                "sector": "IT",
                "quantity": 10,
                "average_price": 100.0,
                "current_price": 120.0,
                "day_change_percent": 1.5,
            },
            {
                "symbol": "TCS",
                "sector": "IT",
                "quantity": 5,
                "average_price": 200.0,
                "current_price": 220.0,
                "day_change_percent": 0.5,
            },
        ]
    }

    response = client.post(
        "/api/v1/portfolio/analyze",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert "summary" in data
    assert "holdings" in data
    assert "hhi" in data["summary"]


def test_portfolio_holdings_endpoint():
    response = client.get("/api/v1/portfolio/holdings")

    assert response.status_code == 200

    data = response.json()

    assert "holdings" in data
    assert "source" in data
    assert isinstance(data["holdings"], list)


def test_watchlist_get_endpoint():
    response = client.get("/api/v1/watchlist")

    assert response.status_code == 200

    data = response.json()

    assert "symbols" in data
    assert isinstance(data["symbols"], list)


def test_watchlist_put_endpoint():
    payload = {
        "symbols": [
            "INFY",
            "TCS",
        ]
    }

    response = client.put(
        "/api/v1/watchlist",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["symbols"] == [
        "INFY",
        "TCS",
    ]


def test_activity_endpoint():
    response = client.get("/api/v1/activity")

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "items" in data
    assert isinstance(data["count"], int)
    assert isinstance(data["items"], list)


def test_operations_metrics_endpoint():
    response = client.get("/api/v1/operations/metrics")

    assert response.status_code == 200

    data = response.json()

    expected_fields = [
        "api_requests",
        "api_success_rate",
        "api_average_latency_ms",
        "api_errors",
        "ai_requests",
        "ai_success_rate",
        "ai_errors",
        "tool_calls",
        "tool_success_rate",
        "tool_average_latency_ms",
        "alpha_vantage_requests_used",
        "alpha_vantage_daily_limit",
    ]

    for field in expected_fields:
        assert field in data


def test_portfolio_analyze_rejects_invalid_payload():
    payload = {
        "holdings": [
            {
                "symbol": "INFY",
                "quantity": "invalid",
            }
        ]
    }

    response = client.post(
        "/api/v1/portfolio/analyze",
        json=payload,
    )

    assert response.status_code == 422
