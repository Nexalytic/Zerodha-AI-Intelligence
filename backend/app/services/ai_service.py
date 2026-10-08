from __future__ import annotations
import json
import os
import re
from typing import Any
import httpx
from app.demo_store import (
    complete_analysis_run,
    create_analysis_run,
    record_audit_event,
    record_recommendation,

)
from app.models.analysis import AnalyzeRequest
from app.models.portfolio import Holding
from app.models.recommendation import Recommendation
from app.orchestrator.orchestrator import WorkflowOrchestrator
from app.recommendations.engine import generate_recommendations
from app.validation.recommendation_validator import validate_recommendation
from app.services.portfolio_service import analyze_portfolio
from app.tools.registry import TOOL_REGISTRY
GROQ_API_BASE = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_TEXT_FALLBACKS = ["llama-3.1-8b-instant"]
_GROQ_SEARCH_FALLBACKS = ["groq/compound-mini"]
def _is_market_query(question: str) -> bool:
    return bool(
        re.search(
            r"\b(market|news|latest|sector outlook)\b|current\s+(market|price|news)|"
            r"\b(stock|share)\s+price\b|\blive\s+(market|price|news)\b",
            question,
            re.I,
        )
    )
def _local_portfolio_answer(question: str, analysis: dict[str, Any]) -> str:
    summary = analysis["summary"]
    holdings = analysis["holdings"]
    winners = sorted(holdings, key=lambda h: h["pnl"], reverse=True)
    sectors = analysis["sector_allocation"]
    if not holdings:
        return "There are no confirmed holdings in this session yet. Import a CSV and confirm the rows before asking portfolio questions."
    if re.search(r"full review|complete review|all available|all aspects", question, re.I):
        top_position = max(holdings, key=lambda h: h["market_value"])
        best = sorted(holdings, key=lambda h: h["pnl"], reverse=True)[:3]
        worst = sorted(holdings, key=lambda h: h["pnl"])[:3]
        sector_text = "; ".join(
            f"{s['sector']} {s['weight_percent']:.1f}%" for s in sectors
        ) or "Unavailable"
        return (
            f"PORTFOLIO SNAPSHOT: {summary['holding_count']} holdings; market value "
            f"{summary['market_value']:,.0f} INR; invested {summary['invested_value']:,.0f} INR; "
            f"unrealized P&L {summary['pnl']:+,.0f} INR ({summary['pnl_percent']:+.2f}%).\n\n"
            f"CONCENTRATION: HHI {summary['hhi']:.3f}; largest position "
            f"{top_position['symbol']} at "
            f"{top_position['market_value']/summary['market_value']*100:.1f}% of value.\n\n"
            f"SECTORS: {sector_text}.\n\n"
            "TOP UNREALIZED CONTRIBUTORS: "
            + "; ".join(
                f"{h['symbol']} {h['pnl']:+,.0f} INR ({h['pnl_percent']:+.2f}%)"
                for h in best
            )
            + ".\n\n"
            "LOWEST UNREALIZED P&L: "
            + "; ".join(
                f"{h['symbol']} {h['pnl']:+,.0f} INR ({h['pnl_percent']:+.2f}%)"
                for h in worst
            )
            + ".\n\n"
            "LIMITS: Prices are user supplied and not verified live. There is no dated "
            "return history, so daily attribution, volatility, maximum drawdown, Sharpe, "
            "beta, correlation, benchmark comparison, taxes and dividends cannot be "
            "calculated from this snapshot."
        )
    if re.search(r"risk|concentrat|diversif|exposure", question, re.I):
        top_market = max(holdings, key=lambda h: h["market_value"])
        sector = sectors[0] if sectors else None
        return (
            f"From the confirmed snapshot: HHI concentration is {summary['hhi']:.3f} "
            f"(higher values mean more weight in fewer names). "
            f"{top_market['symbol']} is the largest position at "
            f"{top_market['market_value']/summary['market_value']*100:.1f}% of current value. "
            f"{sector['sector']} is the largest sector at {sector['weight_percent']:.1f}%. "
            "Historical volatility, drawdown, beta and correlation need dated price history "
            "and are not inferred from this snapshot."
        )
    if re.search(r"winner|best|gain|contribut", question, re.I):
        chosen = winners[:3]
        return (
            "Largest unrealized P&L contributors in this snapshot: "
            + "; ".join(
                f"{h['symbol']} {h['pnl']:+,.0f} INR ({h['pnl_percent']:+.2f}%)"
                for h in chosen
            )
            + ". These use the imported average cost and price, before fees, taxes and dividends."
        )
    if re.search(r"loser|losing|worst|losses|underperform|\bdown\b", question, re.I):
        chosen = sorted(holdings, key=lambda h: h["pnl"])[:3]
        return (
            "Lowest unrealized P&L positions in this snapshot: "
            + "; ".join(
                f"{h['symbol']} {h['pnl']:+,.0f} INR ({h['pnl_percent']:+.2f}%)"
                for h in chosen
            )
            + ". This identifies snapshot performance; it does not explain causation."
        )
    if re.search(r"sector|allocation", question, re.I):
        return (
            "Sector weights by current value: "
            + "; ".join(
                f"{x['sector']} {x['weight_percent']:.1f}%" for x in sectors
            )
            + ". Sector labels come from your uploaded file or Unclassified defaults."
        )
    if re.search(r"nifty|sensex|benchmark|compare", question, re.I):
        return (
            "A portfolio-versus-index comparison is unavailable because this session has "
            "no dated portfolio history or verified benchmark series. I won't infer relative "
            "performance from one snapshot."
        )
    if re.search(r"why|today|changed|cause|fell|drop|movement", question, re.I):
        return (
            f"The snapshot shows {summary['pnl']:+,.0f} INR unrealized P&L overall, but it "
            "does not contain verified dated prices or market events. I can't attribute a "
            "daily move or explain its cause without time-stamped portfolio history and "
            "sourced market data."
        )
    return (
        f"Confirmed portfolio snapshot: market value {summary['market_value']:,.0f} INR; "
        f"invested value {summary['invested_value']:,.0f} INR; unrealized P&L "
        f"{summary['pnl']:+,.0f} INR ({summary['pnl_percent']:+.2f}%); "
        f"{summary['holding_count']} holdings. I can break down sector weights, "
        "concentration, largest winners or lowest P&L positions. Prices are user-supplied "
        "and not live quotes."
    )
def _extract_groq_citations(message: dict[str, Any]) -> list[dict[str, str]]:
    citations: list[dict[str, str]] = []
    seen: set[str] = set()
    def _add(url: str | None, title: str | None) -> None:
        if url and url not in seen:
            seen.add(url)
            citations.append({"title": title or "Source", "url": url})
    for annotation in message.get("annotations") or []:
        url_citation = annotation.get("url_citation") or {}
        _add(
            url_citation.get("url") or annotation.get("url"),
            url_citation.get("title") or annotation.get("title"),
        )
    for tool in message.get("executed_tools") or []:
        results = tool.get("search_results") or []
        if isinstance(results, dict):
            results = results.get("results", [])
        for result in results or []:
            if isinstance(result, dict):
                _add(
                    result.get("url") or result.get("link"),
                    result.get("title") or result.get("name"),
                )
    return citations
async def answer_question(
    question: str,
    holdings: list[Any],
) -> dict[str, Any]:
    question = question.strip()

    run_id = create_analysis_run(
        "local-demo-user",
        question,
    )

    record_audit_event(
        run_id,
        "ANALYSIS_STARTED",
        "Portfolio analysis started.",
        {"question": question},
    )
    orchestrator = WorkflowOrchestrator(TOOL_REGISTRY)
    normalized_holdings = [
        Holding.model_validate(holding)
        if not isinstance(holding, Holding)
        else holding
        for holding in holdings
    ]
    orchestration = await orchestrator.execute_tools(
        question,
        holdings=normalized_holdings,
          run_id=run_id,
    )
    record_audit_event(
        run_id,
        "TOOLS_COMPLETED",
        "Required analysis tools completed.",
        {
            "tools": orchestration.get("tools", []),
        },
    )
    market_query = _is_market_query(question)
    if holdings:
        analysis = analyze_portfolio(normalized_holdings)
    else:
        analysis = {
            "summary": {
                "market_value": 0,
                "invested_value": 0,
                "pnl": 0,
                "pnl_percent": 0,
                "holding_count": 0,
                "hhi": 0,
            },
            "holdings": [],
            "sector_allocation": [],
        }
    record_audit_event(
        run_id,
        "ANALYTICS_COMPLETED",
        "Portfolio analytics generated.",
        {
            "holding_count": analysis["summary"]["holding_count"],
            "market_value": analysis["summary"]["market_value"],
            "pnl": analysis["summary"]["pnl"],
        },
    )
    recommendations = generate_recommendations(normalized_holdings)
    record_audit_event(
        run_id,
        "RECOMMENDATIONS_GENERATED",
        "Recommendation engine generated recommendations.",
        {
            "count": len(recommendations),
        },
    )
    validated_recommendations: list[Recommendation] = []
    for recommendation in recommendations:
        validation = validate_recommendation(
            recommendation,
            analysis,
        )
        record_audit_event(
            run_id,
            "RECOMMENDATION_VALIDATED",
            "Recommendation validation completed.",
            {
                "type": recommendation.type,
                "symbol": recommendation.symbol,
                "status": validation.status,
                "errors": validation.errors,
                "warnings": validation.warnings,
            },
        )

        if validation.status == "PASS":
            validated_recommendations.append(recommendation)

            record_recommendation(
                run_id,
                recommendation.model_dump(),
                validation.status,
            )
    record_audit_event(
        run_id,
        "VALIDATION_COMPLETED",
        "Recommendation validation stage completed.",
        {
            "generated_count": len(recommendations),
            "validated_count": len(validated_recommendations),
        },
    )

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        if market_query:
            complete_analysis_run(
                run_id,
                status="COMPLETED",
                mode="market_unavailable",
            )
            return {
                "answer": "Live market and news search is unavailable because GROQ_API_KEY is not configured. Portfolio questions can still be answered from your confirmed holdings.",
                "mode": "market_unavailable",
                "citations": [],
                "evidence": [],
                "limitations": [
                    "Current news search needs a Groq API key; check Alpha Vantage separately for quote availability."
                ],
            }
        complete_analysis_run(
            run_id,
            status="COMPLETED",
            mode="evidence_fallback",
        )

        return {
            "answer": _local_portfolio_answer(question, analysis),
            "mode": "evidence_fallback",
            "citations": [],
            "evidence": analysis["summary"],
            "limitations": [
                "Rule-based answer; configure GROQ_API_KEY for AI explanations.",
                "Portfolio prices can be CSV-supplied or updated with an Alpha Vantage quote; check its data date.",
            ],
            "recommendations": [
                recommendation.model_dump()
                for recommendation in validated_recommendations
            ],
        }
    if market_query:
        configured_model = (
            os.getenv("GROQ_SEARCH_MODEL", "groq/compound") or "groq/compound"
        ).strip()
        fallbacks = _GROQ_SEARCH_FALLBACKS
    else:
        configured_model = (
            os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
            or "llama-3.3-70b-versatile"
        ).strip()
        fallbacks = _GROQ_TEXT_FALLBACKS
    models_to_try = [configured_model] + [
        m for m in fallbacks if m != configured_model
    ]
    system_prompt = (
        "You are a careful Indian-market portfolio analyst. Explain, do not instruct trades "
        "or guarantee returns. All calculations in the supplied portfolio context are "
        "deterministic. Never invent a holding, price, metric, news item, or source. "
        "Recommendations supplied in the context are deterministic Python-generated outputs. "
        "Do not invent, modify, or recalculate their evidence, severity, action, or confidence. "
        "For portfolio statements cite the exact supplied evidence and note limitations. "
        "For current market/news questions use your web search tool and cite sources. "
        "If data is unavailable say so. Give a direct, plain-English answer and distinguish "
        "facts from interpretation."
    )
    context = {
        "question": question,
        "context_purpose": "Explain verified facts and validated recommendations only.",
        "calculation_authority": "Python analytics",
        "recommendation_authority": "Validated Python recommendation engine",
        "orchestration": orchestration,
        "recommendations": [
            recommendation.model_dump()
            for recommendation in validated_recommendations
        ],
    }
    if not market_query:
         context.update(
            {
                "portfolio_analytics": analysis,
                "portfolio_data_quality": {
                    "prices": "user supplied, not verified live",
                    "history": "unavailable",
                },
            }
    )
    request_body: dict[str, Any] = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(context, ensure_ascii=False),
            },
        ],
        "temperature": 0.2,
    }
    if market_query:
        request_body["tools"] = [{"type": "browser_search"}]
        request_body["tool_choice"] = "required"
    used_model = models_to_try[0]
    error_detail: str | None = None
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response: httpx.Response | None = None
            for candidate_model in models_to_try:
                body = {**request_body, "model": candidate_model}
                response = await client.post(
                    GROQ_API_BASE,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=body,
                )
                used_model = candidate_model
                if response.status_code in (404, 400):
                    try:
                        msg = response.json().get("error", {}).get("message", "")
                    except ValueError:
                        msg = ""
                    if response.status_code == 404 or "model" in msg.lower():
                        error_detail = (
                            f"Groq model '{candidate_model}' was rejected: "
                            f"{msg or response.status_code}."
                        )
                        continue
                break
            assert response is not None
            if response.status_code >= 400:
                try:
                    error_detail = (
                        response.json().get("error", {}).get("message")
                        or error_detail
                    )
                except ValueError:
                    error_detail = response.text[:300] or error_detail
            response.raise_for_status()
        data = response.json()
        message = (data.get("choices") or [{}])[0].get("message", {})
        text = (message.get("content") or "").strip()

        if text:
            record_audit_event(
                run_id,
                "AI_EXPLANATION_GENERATED",
                "AI explanation generated successfully.",
                {
                    "model": used_model,
                    "response_length": len(text),
                },
            )
        citations = _extract_groq_citations(message) if market_query else []
        finish_reason = (data.get("choices") or [{}])[0].get("finish_reason")
        if not text and finish_reason and finish_reason != "stop":
            error_detail = (
                f"Groq stopped early ({finish_reason}) and returned no text; "
                "try rephrasing the question."
            )
        response_mode = (
            "groq_grounded"
            if market_query and citations
            else "groq_no_sources"
            if market_query
            else "groq_portfolio"
        )
        response_limitations = (
            []
            if citations
            else ["No web citations were returned; verify current-market statements independently."]
            if market_query
            else ["Portfolio prices are user-supplied and have not been verified against a market provider."]
        )
        if used_model != configured_model:
            response_limitations.append(
                f"Configured Groq model '{configured_model}' was unavailable; used "
                f"'{used_model}' instead. Update GROQ_MODEL/GROQ_SEARCH_MODEL in "
                "backend/.env once you confirm the right model id for your key."
            )

        complete_analysis_run(
            run_id,
            status="COMPLETED",
            mode=response_mode,
        )
        return {
            "answer": text or "The model returned no answer. Please try again.",
            "mode": response_mode,
            "citations": citations,
            "evidence": analysis["summary"],
            "limitations": response_limitations,
            "recommendations": [
                recommendation.model_dump()
                for recommendation in validated_recommendations
            ],
        }
    except (httpx.HTTPError, ValueError, KeyError, IndexError) as exc:
        detail = error_detail or type(exc).__name__
        if market_query:
            complete_analysis_run(
                run_id,
                status="COMPLETED",
                mode="market_unavailable",
                error=detail,
            )
            return {
                "answer": "I couldn't retrieve grounded market or news information just now. Please try again later.",
                "mode": "market_unavailable",
                "citations": [],
                "evidence": [],
                "limitations": [detail],
            }
        complete_analysis_run(
            run_id,
            status="COMPLETED",
            mode="evidence_fallback",
            error=detail,
        )
        return {
            "answer": _local_portfolio_answer(question, analysis),
            "mode": "evidence_fallback",
            "citations": [],
            "evidence": analysis["summary"],
            "limitations": [
                "Groq was unavailable; this answer uses deterministic portfolio evidence only.",
                detail,
            ],
        }