from src.graph.state import AnalysisState, CompanyInfo
from src.nodes.prompts import REPORT_PROMPT
from src.shared.llm import get_llm

llm = get_llm()


async def report(state: AnalysisState) -> AnalysisState:
    try:
        company_info: CompanyInfo | None = state.get("company_info")
        if not company_info:
            return {**state, "error": "No company information available for report"}

        key_events = state.get("key_events", [])
        key_events_str = ", ".join(key_events) if key_events else "No events"

        prompt = REPORT_PROMPT.format(
            name=company_info["name"],
            ticker=state["ticker"],
            price=company_info["price"],
            market_cap=company_info["market_cap"],
            sector=company_info["sector"],
            industry=company_info["industry"],
            pe_ratio=company_info["pe_ratio"],
            eps=company_info["eps"],
            fifty_two_week_high=company_info["fifty_two_week_high"],
            fifty_two_week_low=company_info["fifty_two_week_low"],
            dividend_yield=company_info["dividend_yield"],
            revenue_growth=company_info["revenue_growth"],
            gross_margins=company_info["gross_margins"],
            profit_margins=company_info["profit_margins"],
            return_on_equity=company_info["return_on_equity"],
            debt_to_equity=company_info["debt_to_equity"],
            free_cashflow=company_info["free_cashflow"],
            total_cash=company_info["total_cash"],
            total_debt=company_info["total_debt"],
            sentiment=state.get("sentiment", "N/A"),
            key_events=key_events_str,
        )

        response = await llm.ainvoke(prompt)

        content = response.content
        if isinstance(content, list):
            content = "".join(
                item if isinstance(item, str) else str(item) for item in content
            )

        return {
            **state,
            "report": content,
        }
    except Exception as e:
        return {**state, "error": f"Report generation error: {str(e)}"}
