import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.schemas.GenerateReportRequest import GenerateReportRequest
from src.graph.graph import graph

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/generate_report")
async def generate_report(req: GenerateReportRequest):
    app = graph.compile()
    result = await app.ainvoke(
        {"ticker": req.ticker, "valid_ticker": False, "error": None}
    )
    print(result)
    return result
