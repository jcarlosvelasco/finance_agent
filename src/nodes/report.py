import logging
from datetime import date

from langfuse.client import StatefulSpanClient
from langgraph.types import interrupt

from src.graph.state import AnalysisState
from src.langfuse import langfuse
from src.nodes.prompts import REPORT_PROMPT
from src.shared.llm import get_llm

llm = get_llm()
logger = logging.getLogger(__name__)


def safe_float(value, default=0.0) -> float:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _format_for_review(state: AnalysisState) -> dict:
    ci = state.company_info
    return {
        "ticker": state.ticker,
        "company": {
            "name": ci.name if ci else "N/A",
            "price": ci.price if ci else None,
            "market_cap": ci.market_cap if ci else None,
            "sector": ci.sector if ci else None,
            "pe_ratio": ci.pe_ratio if ci else None,
            "eps": ci.eps if ci else None,
            "dividend_yield": ci.dividend_yield if ci else None,
            "52w_high": ci.fifty_two_week_high if ci else None,
            "52w_low": ci.fifty_two_week_low if ci else None,
            "revenue_growth": ci.revenue_growth if ci else None,
            "gross_margins": ci.gross_margins if ci else None,
            "profit_margins": ci.profit_margins if ci else None,
            "debt_to_equity": ci.debt_to_equity if ci else None,
            "return_on_equity": ci.return_on_equity if ci else None,
        },
        "sentiment": state.sentiment or "N/A",
        "key_events": state.key_events or [],
        "news_count": len(state.news_items or []),
    }


async def report(state: AnalysisState) -> dict:
    company_info = state.company_info
    if not company_info:
        return {"error": "No company information available for report"}

    review_data = _format_for_review(state)
    human_input = interrupt(review_data)

    if not human_input.get("approved"):
        fb = human_input.get("feedback", "")
        return {
            "report": None,
            "error": f"Report rejected by user: {fb}"
            if fb
            else "Report rejected by user",
            "human_feedback": fb or None,
            "human_approved": False,
        }

    span: StatefulSpanClient | None = None
    trace = langfuse.trace(name="reports_node")

    try:
        key_events = state.key_events or []
        key_events_str = ", ".join(key_events) if key_events else "No events"

        prompt = REPORT_PROMPT.format(
            current_date=date.today().strftime("%B %d, %Y"),
            name=company_info.name or "N/A",
            ticker=state.ticker,
            price=safe_float(company_info.price),
            market_cap=safe_float(company_info.market_cap),
            sector=company_info.sector or "N/A",
            industry=company_info.industry or "N/A",
            pe_ratio=safe_float(company_info.pe_ratio),
            eps=safe_float(company_info.eps),
            fifty_two_week_high=safe_float(company_info.fifty_two_week_high),
            fifty_two_week_low=safe_float(company_info.fifty_two_week_low),
            dividend_yield=safe_float(company_info.dividend_yield),
            revenue_growth=safe_float(company_info.revenue_growth),
            gross_margins=safe_float(company_info.gross_margins),
            profit_margins=safe_float(company_info.profit_margins),
            return_on_equity=safe_float(company_info.return_on_equity),
            debt_to_equity=safe_float(company_info.debt_to_equity),
            free_cashflow=safe_float(company_info.free_cashflow),
            total_cash=safe_float(company_info.total_cash),
            total_debt=safe_float(company_info.total_debt),
            sentiment=state.sentiment or "N/A",
            key_events=key_events_str,
        )

        span = trace.span(name="llm_report", input={"prompt": prompt})

        response = await llm.ainvoke(prompt)
        logger.info("LLM response: %s", response.content)

        span.end(output=response.content)
        content = response.content

        if isinstance(content, list):
            content = "".join(
                item if isinstance(item, str) else str(item) for item in content
            )

        return {"report": content, "human_approved": True}

    except Exception as e:
        trace.update(
            metadata={
                "error": str(e),
                "status": "failed",
                "ticker": state.ticker,
            }
        )
        if span is not None:
            span.end(output={"error": str(e)})
        return {"error": f"Report generation error: {str(e)}"}
