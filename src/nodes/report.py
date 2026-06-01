import logging

from langfuse.client import StatefulSpanClient

from src.graph.state import AnalysisState, CompanyInfo
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


async def report(state: AnalysisState) -> AnalysisState:
    span: StatefulSpanClient | None = None
    trace = langfuse.trace(name="reports_node")

    try:
        company_info: CompanyInfo | None = state.get("company_info")
        if not company_info:
            return {**state, "error": "No company information available for report"}

        key_events = state.get("key_events", [])
        key_events_str = ", ".join(key_events) if key_events else "No events"

        prompt = REPORT_PROMPT.format(
            name=company_info.get("name") or "N/A",
            ticker=state["ticker"],
            price=safe_float(company_info.get("price")),
            market_cap=safe_float(company_info.get("market_cap")),
            sector=company_info.get("sector") or "N/A",
            industry=company_info.get("industry") or "N/A",
            pe_ratio=safe_float(company_info.get("pe_ratio")),
            eps=safe_float(company_info.get("eps")),
            fifty_two_week_high=safe_float(company_info.get("fifty_two_week_high")),
            fifty_two_week_low=safe_float(company_info.get("fifty_two_week_low")),
            dividend_yield=safe_float(company_info.get("dividend_yield")),
            revenue_growth=safe_float(company_info.get("revenue_growth")),
            gross_margins=safe_float(company_info.get("gross_margins")),
            profit_margins=safe_float(company_info.get("profit_margins")),
            return_on_equity=safe_float(company_info.get("return_on_equity")),
            debt_to_equity=safe_float(company_info.get("debt_to_equity")),
            free_cashflow=safe_float(company_info.get("free_cashflow")),
            total_cash=safe_float(company_info.get("total_cash")),
            total_debt=safe_float(company_info.get("total_debt")),
            sentiment=state.get("sentiment", "N/A"),
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

        return {**state, "report": content}

    except Exception as e:
        trace.update(
            metadata={
                "error": str(e),
                "status": "failed",
                "ticker": state.get("ticker"),
            }
        )
        if span is not None:
            span.end(output={"error": str(e)})
        return {**state, "error": f"Report generation error: {str(e)}"}
