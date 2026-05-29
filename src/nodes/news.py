import logging
import os

from tavily import TavilyClient

from src.graph.state import AnalysisState
from src.nodes.prompts import SENTIMENT_PROMPT
from src.shared.llm import SentimentResponse, get_structured_llm

tavily_api_key = os.getenv("TAVILY_API_KEY")


tavily = TavilyClient(api_key=tavily_api_key)
llm = get_structured_llm(SentimentResponse)
logger = logging.getLogger(__name__)


async def news(state: AnalysisState) -> AnalysisState:
    try:
        results = tavily.search(
            query=f"{state['ticker']} {state.get('company_name', '')} stock news",
            max_results=8,
            topic="news",
        )
        headlines = [r["title"] for r in results["results"]]

        analysis = await llm.ainvoke(
            SENTIMENT_PROMPT.format(
                company=state.get("company_name", state["ticker"]),
                headlines="\n".join(headlines),
            )
        )

        logger.info(f"RAW LLM RESPONSE: {repr(analysis)}")
        logger.info(f"RAW LLM TYPE: {type(analysis)}")

        analysis = SentimentResponse.model_validate(analysis)

        logger.info(f"Sentiment analysis: {analysis}")

        return {
            **state,
            "news_items": results["results"],
            "sentiment": analysis.sentiment,
            "key_events": analysis.key_events,
        }
    except Exception as e:
        return {**state, "error": str(e)}
