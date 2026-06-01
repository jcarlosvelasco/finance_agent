import logging
from contextlib import asynccontextmanager
from typing import cast

from fastapi import Depends, FastAPI

from src.api.schemas.GenerateReportRequest import GenerateReportRequest
from src.graph.graph import graph
from src.graph.state import AnalysisState
from src.nodes.save_report import load_cached_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/generate_report")
async def generate_report(req: GenerateReportRequest = Depends()):
    ticker = req.ticker.upper()

    cached = load_cached_report(ticker)
    if cached:
        logger.info(f"Cache hit for {ticker}")
        return {"success": True, "report": cached["report"]}

    compiled = graph.compile()
    initial_state = cast(
        AnalysisState,
        {
            "ticker": req.ticker,
            "valid_ticker": False,
            "error": None,
            "company_info": None,
            "news_items": None,
            "sentiment": None,
            "key_events": None,
            "report": None,
        },
    )
    result = await compiled.ainvoke(initial_state)

    if result["error"]:
        logger.error(f"Error generating report for {ticker}: {result['error']}")
        return {"success": False, "error": result["error"]}

    return {"success": True, "report": result["report"]}
