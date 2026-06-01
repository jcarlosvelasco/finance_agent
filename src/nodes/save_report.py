import json
import logging
from datetime import date, datetime
from pathlib import Path

from src.graph.state import AnalysisState

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent.parent / "data" / "reports"


def get_cache_path(ticker: str) -> Path:
    if not REPORTS_DIR.exists():
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    return REPORTS_DIR / f"{ticker.upper()}.json"


def load_cached_report(ticker: str) -> dict | None:
    path = get_cache_path(ticker)

    if not path.exists():
        return None

    mtime = datetime.fromtimestamp(path.stat().st_mtime).date()
    if mtime != date.today():
        return None

    return json.loads(path.read_text(encoding="utf-8"))


async def save_report(state: AnalysisState) -> AnalysisState:

    return state
