import asyncio
import logging
import os

from langfuse.client import StatefulSpanClient

from src.graph.state import AnalysisState, CompanyInfo
from src.langfuse import langfuse
from src.shared.llm import get_llm
from src.tools.yfinance_tools import get_financials, get_stock_info

provider = os.getenv("LLM_PROVIDER", "ollama")

logger = logging.getLogger(__name__)

tools = [get_stock_info, get_financials]
llm = get_llm()
agent = llm.bind_tools(tools)


async def fundamentals(state: AnalysisState) -> dict:
    trace = langfuse.trace(name="fundamentals_node")
    stock_span: StatefulSpanClient | None = None
    financials_span: StatefulSpanClient | None = None

    try:
        ticker = state.ticker

        stock_span = trace.span(name="get_stock_info", input={"ticker": ticker})
        financials_span = trace.span(name="get_financials", input={"ticker": ticker})

        stock_task = get_stock_info.ainvoke(ticker)
        financials_task = get_financials.ainvoke(ticker)

        stock_info, financials = await asyncio.gather(stock_task, financials_task)

        stock_span.end(output=stock_info)
        financials_span.end(output=financials)

        company_info = CompanyInfo(
            name=stock_info.name,
            price=stock_info.price,
            market_cap=stock_info.market_cap,
            pe_ratio=stock_info.pe_ratio,
            eps=stock_info.eps,
            fifty_two_week_high=stock_info.fifty_two_week_high,
            fifty_two_week_low=stock_info.fifty_two_week_low,
            dividend_yield=stock_info.dividend_yield,
            sector=stock_info.sector,
            industry=stock_info.industry,
            revenue_growth=financials.revenue_growth,
            gross_margins=financials.gross_margins,
            profit_margins=financials.profit_margins,
            debt_to_equity=financials.debt_to_equity,
            return_on_equity=financials.return_on_equity,
            free_cashflow=financials.free_cashflow,
            total_cash=financials.total_cash,
            total_debt=financials.total_debt,
        )

        return {"company_info": company_info}
    except Exception as e:
        trace.update(
            metadata={
                "error": str(e),
                "status": "failed",
                "ticker": state.ticker,
            }
        )

        try:
            if stock_span is not None:
                stock_span.end()
            if financials_span is not None:
                financials_span.end()
        except Exception:
            pass

        logger.error(f"\nError in fundamentals: {str(e)}")
        return {"error": str(e)}
