from typing import List

from typing_extensions import TypedDict


class CompanyInfo(TypedDict):
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
    revenue_growth: float
    gross_margins: float
    profit_margins: float
    debt_to_equity: float
    return_on_equity: float
    free_cashflow: float
    total_cash: float
    total_debt: float


class AnalysisState(TypedDict):
    ticker: str
    valid_ticker: bool
    error: str | None

    company_info: CompanyInfo | None

    news_items: List[dict] | None
    sentiment: str | None
    key_events: List[str] | None

    report: str | None

    evaluation: dict | None

    human_feedback: str | None
    human_approved: bool | None
