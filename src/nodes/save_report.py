import json
import logging
from datetime import date
from pathlib import Path

from src.graph.state import AnalysisState

REPORTS_DIR = Path("reports")
logger = logging.getLogger(__name__)


def get_cache_path(ticker: str) -> Path:
    today = date.today().isoformat()
    REPORTS_DIR.mkdir(exist_ok=True)
    return REPORTS_DIR / f"{ticker.upper()}_{today}.json"


def load_cached_report(ticker: str) -> dict | None:
    path = get_cache_path(ticker)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


async def save_report(state: AnalysisState) -> AnalysisState:
    path = get_cache_path(state["ticker"])
    payload = {
        "ticker": state["ticker"],
        "company_info": state["company_info"],
        "sentiment": state["sentiment"],
        "key_events": state["key_events"],
        "report": state["report"],
        "generated_at": date.today().isoformat(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info(f"Report saved to {path}")
    return state
