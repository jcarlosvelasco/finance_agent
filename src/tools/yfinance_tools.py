import yfinance as yf
from langchain_core.tools import tool


@tool
def get_stock_info(ticker: str) -> dict:
    """Get current stock price and key metrics for a ticker."""
    stock = yf.Ticker(ticker)
    info = stock.info
    return {
        "name": info.get("longName"),
        "price": info.get("currentPrice"),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "eps": info.get("trailingEps"),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow"),
        "dividend_yield": info.get("dividendYield"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
    }


@tool
def get_financials(ticker: str) -> dict:
    """Get income statement and balance sheet summary."""
    stock = yf.Ticker(ticker)
    info = stock.info
    return {
        "revenue_growth": info.get("revenueGrowth"),
        "gross_margins": info.get("grossMargins"),
        "profit_margins": info.get("profitMargins"),
        "debt_to_equity": info.get("debtToEquity"),
        "return_on_equity": info.get("returnOnEquity"),
        "free_cashflow": info.get("freeCashflow"),
        "total_cash": info.get("totalCash"),
        "total_debt": info.get("totalDebt"),
    }
