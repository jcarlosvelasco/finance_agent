import yfinance as yf

from src.graph.state import AnalysisState


def supervisor(state: AnalysisState) -> dict:
    ticker = state.ticker

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        exists = info is not None and info.get("symbol") is not None

        if not exists:
            return {"valid_ticker": exists, "error": f"Ticker '{ticker}' does not exist"}

        return {"valid_ticker": exists, "error": None}

    except Exception as e:
        return {"valid_ticker": False, "error": str(e)}
