import yfinance as yf

from src.graph.state import AnalysisState


def supervisor(state: AnalysisState) -> AnalysisState:
    ticker = state["ticker"]

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        exists = info is not None and info.get("symbol") is not None

        state["valid_ticker"] = exists

        if not exists:
            state["error"] = f"Ticker '{ticker}' does not exist"
        else:
            state["error"] = None

    except Exception as e:
        state["valid_ticker"] = False
        state["error"] = str(e)

    return state
