import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from src.api.schemas.GenerateReportRequest import GenerateReportRequest
from src.graph.graph import graph
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
        return {"success": True, "report": cached}

    app = graph.compile()
    result = await app.ainvoke(
        {
            "ticker": req.ticker,
            "valid_ticker": False,
            "error": None,
            "company_info": None,
            "news_items": None,
            "sentiment": None,
            "key_events": None,
            "report": None,
        }
    )

    if result["error"]:
        logger.error(f"Error generating report for {ticker}: {result['error']}")
        return {"success": False, "error": result["error"]}

    return {"success": True, "report": result["report"]}
