from __future__ import annotations

from typing import Any
import time
from app.demo_store import record_tool_call
from app.models.portfolio import Holding


class WorkflowOrchestrator:
    """
    Coordinates request understanding, tool selection,
    tool execution, evidence collection, and AI response generation.
    """

    def __init__(self, tool_registry: dict[str, Any]):
        self.tool_registry = tool_registry

    def select_tools(self, question: str) -> list[str]:
        """
        Select the tools required for the user's request.

        Phase 3 starts with simple deterministic routing.
        More advanced routing can be added later.
        """
        question_lower = question.lower()
        selected: list[str] = []

        if any(
            word in question_lower
            for word in ["portfolio", "holding", "investment"]
        ):
            selected.append("get_portfolio")

        if any(
            word in question_lower
            for word in ["risk", "concentration", "diversification"]
        ):
            selected.append("calculate_concentration")

        if any(
            word in question_lower
            for word in ["sector", "allocation"]
        ):
            selected.append("calculate_sector_allocation")

        if any(
            word in question_lower
            for word in ["price", "quote", "current"]
        ):
            selected.append("get_quote")

        if not selected:
            selected.append("get_portfolio")

        return selected

    async def execute_tools(
        self,
        question: str,
        user: str = "demo_user",
        holdings: list[Holding] | None = None,
        run_id: int | None = None,
    ) -> dict[str, Any]:
        selected_tools = self.select_tools(question)
        evidence: dict[str, Any] = {}

        for tool_name in selected_tools:
            tool = self.tool_registry[tool_name]
            tool_started_at = time.time()

            if tool_name == "get_quote":
                result = await tool("INFY")
            elif tool_name in {
                "get_portfolio",
                "calculate_portfolio_metrics",
                "calculate_sector_allocation",
                "calculate_concentration",
            }:
                result = tool(user, holdings)
            else:
                result = tool(user)

            if run_id is not None:
                record_tool_call(
                    run_id,
                    tool_name,
                    "SUCCESS",
                    {"question": question},
                    result.model_dump(),
                    tool_started_at,
                    time.time(),
                )

            evidence[tool_name] = result.model_dump()

        return {
            "question": question,
            "tools": selected_tools,
            "evidence": evidence,
        }