import logging
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from langgraph.types import Command

from src.api.schemas.GenerateReportRequest import GenerateReportRequest
from src.api.schemas.ReviewRequest import ReviewRequest
from src.graph.graph import compiled_app
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

    thread_id = f"report_{ticker}"
    initial_state = AnalysisState(
        ticker=req.ticker,
    )
    result = await compiled_app.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": thread_id}},
    )
    result = await compiled_app.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": thread_id}},
    )

    if result.get("human_approved") is False:
        return {
            "success": False,
            "error": result.get("error", "Report rejected"),
            "feedback": result.get("human_feedback"),
        }

    if result.get("__interrupt__"):
        interrupt_val = result["__interrupt__"][0].value
        return {
            "status": "awaiting_review",
            "thread_id": thread_id,
            "data": interrupt_val,
        }

    if result.get("error"):
        logger.error(f"Error generating report for {ticker}: {result['error']}")
        return {"success": False, "error": result["error"]}

    return {"success": True, "report": result["report"]}


@app.post("/review")
async def review_report(body: ReviewRequest):
    result = await compiled_app.ainvoke(
        Command(resume={"approved": body.approved, "feedback": body.feedback}),
        config={"configurable": {"thread_id": body.thread_id}},
    )

    if result.get("human_approved") is False:
        return {
            "success": False,
            "error": result.get("error", "Report rejected"),
            "feedback": result.get("human_feedback"),
        }

    if result.get("error"):
        return {"success": False, "error": result["error"]}

    return {"success": True, "report": result["report"]}
