import pytest

from app.orchestrator.orchestrator import WorkflowOrchestrator


def test_select_tools_for_portfolio_risk_question():
    orchestrator = WorkflowOrchestrator({})

    selected = orchestrator.select_tools(
        "Analyze my portfolio risk and concentration"
    )

    assert selected == [
        "get_portfolio",
        "calculate_concentration",
    ]


def test_select_tools_for_sector_question():
    orchestrator = WorkflowOrchestrator({})

    selected = orchestrator.select_tools(
        "Show my sector allocation"
    )

    assert selected == [
        "calculate_sector_allocation",
    ]


def test_select_tools_for_price_question():
    orchestrator = WorkflowOrchestrator({})

    selected = orchestrator.select_tools(
        "What is the current price?"
    )

    assert selected == ["get_quote"]


def test_select_tools_defaults_to_portfolio():
    orchestrator = WorkflowOrchestrator({})

    selected = orchestrator.select_tools(
        "Hello, help me"
    )

    assert selected == ["get_portfolio"]


@pytest.mark.anyio
async def test_execute_tools_collects_evidence():
    class FakeResult:
        def model_dump(self):
            return {
                "tool": "get_portfolio",
                "status": "success",
                "data": {"count": 1},
            }

    def fake_get_portfolio(user, holdings):
        return FakeResult()

    registry = {
        "get_portfolio": fake_get_portfolio,
    }

    orchestrator = WorkflowOrchestrator(registry)

    result = await orchestrator.execute_tools(
        "Show my portfolio",
        user="test-user",
        holdings=[],
    )

    assert result["question"] == "Show my portfolio"
    assert result["tools"] == ["get_portfolio"]
    assert "get_portfolio" in result["evidence"]
    assert result["evidence"]["get_portfolio"]["status"] == "success"
