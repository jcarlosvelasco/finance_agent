import yfinance as yf
from langchain_core.tools import tool
from langgraph.graph.state import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class GetStockInfoResponse(BaseModel):
    name: str
    price: float
    market_cap: float
    pe_ratio: float
    eps: float
    fifty_two_week_high: float
    fifty_two_week_low: float
    dividend_yield: float
    sector: str
    industry: str


@tool
def get_stock_info(ticker: str) -> GetStockInfoResponse:
    """Get current stock price and key metrics for a ticker."""
    stock = yf.Ticker(ticker)
    info = stock.info
    logger.info(f"Stock info for {ticker}: {info}")
    return GetStockInfoResponse(
        name=info.get("longName"),
        price=info.get("currentPrice"),
        market_cap=info.get("marketCap"),
        pe_ratio=info.get("trailingPE"),
        eps=info.get("trailingEps"),
        fifty_two_week_high=info.get("fiftyTwoWeekHigh"),
        fifty_two_week_low=info.get("fiftyTwoWeekLow"),
        dividend_yield=info.get("dividendYield"),
        sector=info.get("sector"),
        industry=info.get("industry"),
    )


class GetFinancialsResponse(BaseModel):
    revenue_growth: float
    gross_margins: float
    profit_margins: float
    debt_to_equity: float
    return_on_equity: float
    free_cashflow: float
    total_cash: float
    total_debt: float


@tool
def get_financials(ticker: str) -> GetFinancialsResponse:
    """Get income statement and balance sheet summary."""
    stock = yf.Ticker(ticker)
    info = stock.info
    logger.info(f"Financials for {ticker}: {info}")
    response = GetFinancialsResponse(
        revenue_growth=info.get("revenueGrowth"),
        gross_margins=info.get("grossMargins"),
        profit_margins=info.get("profitMargins"),
        debt_to_equity=info.get("debtToEquity"),
        return_on_equity=info.get("returnOnEquity"),
        free_cashflow=info.get("freeCashflow"),
        total_cash=info.get("totalCash"),
        total_debt=info.get("totalDebt"),
    )

    return response
