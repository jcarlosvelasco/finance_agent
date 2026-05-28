import os

from src.graph.state import AnalysisState
from src.shared.llm import get_llm
from src.tools.yfinance_tools import get_financials, get_stock_info

provider = os.getenv("LLM_PROVIDER", "ollama")


tools = [get_stock_info, get_financials]
llm = get_llm()
agent = llm.bind_tools(tools)

SYSTEM = """You are a financial data analyst. Given a stock ticker,
extract key financial metrics using the available tools.
Always call both get_stock_info and get_financials.
Return the raw data — do not interpret yet."""


async def fundamentals(state: AnalysisState) -> AnalysisState:
    try:
        stock_info = get_stock_info.invoke(state["ticker"])
        financials = get_financials.invoke(state["ticker"])
        return {
            "fundamentals": {**stock_info, **financials},
            "company_name": stock_info.get("name"),
        }
    except Exception as e:
        return {"errors": [f"fundamentals_agent failed: {e}"]}
