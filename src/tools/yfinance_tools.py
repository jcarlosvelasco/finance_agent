from typing import Optional

import yfinance as yf
from langchain_core.tools import tool
from langgraph.graph.state import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


def _safe_str(value: object, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _safe_float(value: object, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return default


class GetStockInfoResponse(BaseModel):
    name: str
    price: float
    market_cap: float
    pe_ratio: float
    eps: float
    fifty_two_week_high: float
    fifty_two_week_low: float
    dividend_yield: Optional[float] = None
    sector: str
    industry: str


@tool
def get_stock_info(ticker: str) -> GetStockInfoResponse:
    """Get current stock price and key metrics for a ticker."""
    stock = yf.Ticker(ticker)
    info = stock.info
    logger.info(f"Stock info for {ticker}: {info}")
    return GetStockInfoResponse(
        name=_safe_str(info.get("longName")),
        price=_safe_float(info.get("currentPrice")),
        market_cap=_safe_float(info.get("marketCap")),
        pe_ratio=_safe_float(info.get("trailingPE")),
        eps=_safe_float(info.get("trailingEps")),
        fifty_two_week_high=_safe_float(info.get("fiftyTwoWeekHigh")),
        fifty_two_week_low=_safe_float(info.get("fiftyTwoWeekLow")),
        dividend_yield=_safe_float(info.get("dividendYield")),
        sector=_safe_str(info.get("sector")),
        industry=_safe_str(info.get("industry")),
    )


class GetFinancialsResponse(BaseModel):
    revenue_growth: Optional[float] = None
    gross_margins: Optional[float] = None
    profit_margins: Optional[float] = None
    debt_to_equity: Optional[float] = None
    return_on_equity: Optional[float] = None
    free_cashflow: Optional[float] = None
    total_cash: Optional[float] = None
    total_debt: Optional[float] = None


@tool
def get_financials(ticker: str) -> GetFinancialsResponse:
    """Get income statement and balance sheet summary."""
    stock = yf.Ticker(ticker)
    info = stock.info
    logger.info(f"\nFinancials for {ticker}: {info}")
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
