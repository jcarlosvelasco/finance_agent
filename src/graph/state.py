from pydantic import BaseModel


class CompanyInfo(BaseModel):
    name: str = ""
    price: float = 0.0
    market_cap: float = 0.0
    pe_ratio: float = 0.0
    eps: float = 0.0
    fifty_two_week_high: float = 0.0
    fifty_two_week_low: float = 0.0
    dividend_yield: float = 0.0
    sector: str = ""
    industry: str = ""
    revenue_growth: float = 0.0
    gross_margins: float = 0.0
    profit_margins: float = 0.0
    debt_to_equity: float = 0.0
    return_on_equity: float = 0.0
    free_cashflow: float = 0.0
    total_cash: float = 0.0
    total_debt: float = 0.0


class AnalysisState(BaseModel):
    ticker: str
    valid_ticker: bool = False
    error: str | None = None
    company_info: CompanyInfo | None = None
    news_items: list[dict] | None = None
    sentiment: str | None = None
    key_events: list[str] | None = None
    report: str | None = None
    evaluation: dict | None = None
    human_feedback: str | None = None
    human_approved: bool | None = None
