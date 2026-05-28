from typing_extensions import TypedDict


class AnalysisState(TypedDict):
    ticker: str
    valid_ticker: bool
    error: str | None
