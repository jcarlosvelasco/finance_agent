import os

from src.graph.state import AnalysisState, CompanyInfo
from src.shared.llm import get_llm
from src.tools.yfinance_tools import get_financials, get_stock_info

provider = os.getenv("LLM_PROVIDER", "ollama")


tools = [get_stock_info, get_financials]
llm = get_llm()
agent = llm.bind_tools(tools)


async def fundamentals(state: AnalysisState) -> AnalysisState:
    try:
        stock_info = await get_stock_info.ainvoke(state["ticker"])
        financials = await get_financials.ainvoke(state["ticker"])

        company_info: CompanyInfo = CompanyInfo(
            name=stock_info.get("name"),
            price=stock_info.get("price"),
            market_cap=stock_info.get("market_cap"),
            pe_ratio=stock_info.get("pe_ratio"),
            eps=stock_info.get("eps"),
            fifty_two_week_high=stock_info.get("fifty_two_week_high"),
            fifty_two_week_low=stock_info.get("fifty_two_week_low"),
            dividend_yield=stock_info.get("dividend_yield"),
            sector=stock_info.get("sector"),
            industry=stock_info.get("industry"),
            revenue_growth=financials.get("revenue_growth"),
            gross_margins=financials.get("gross_margins"),
            profit_margins=financials.get("profit_margins"),
            debt_to_equity=financials.get("debt_to_equity"),
            return_on_equity=financials.get("return_on_equity"),
            free_cashflow=financials.get("free_cashflow"),
            total_cash=financials.get("total_cash"),
            total_debt=financials.get("total_debt"),
        )

        return {
            **state,
            "company_info": company_info,
        }
    except Exception as e:
        return {**state, "error": str(e)}
