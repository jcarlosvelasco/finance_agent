import json
import logging
import os
import re

from langchain_core.messages import HumanMessage
from tavily import TavilyClient

from src.graph.state import AnalysisState
from src.nodes.prompts import SENTIMENT_PROMPT
from src.shared.llm import SentimentResponse, get_llm

tavily_api_key = os.getenv("TAVILY_API_KEY")


tavily = TavilyClient(api_key=tavily_api_key)
logger = logging.getLogger(__name__)

llm = get_llm()


def extract_json(text: str) -> dict:
    """Extrae JSON de la respuesta aunque venga con texto alrededor."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    raise ValueError(f"No valid JSON found in response: {text[:200]}")


async def news(state: AnalysisState) -> AnalysisState:
    try:
        results = tavily.search(
            query=f"{state['ticker']} {state.get('company_name', '')} stock news",
            max_results=8,
            topic="news",
        )
        headlines = [r["title"] for r in results["results"]]

        response = await llm.ainvoke(
            [
                HumanMessage(
                    content=SENTIMENT_PROMPT.format(
                        company=state.get("company_name", state["ticker"]),
                        headlines="\n".join(headlines),
                    )
                )
            ]
        )

        logger.info(f"Raw LLM response: {response.content}")

        data = extract_json(response.content)
        analysis = SentimentResponse.model_validate(data)

        return {
            **state,
            "news_items": results["results"],
            "sentiment": analysis.sentiment,
            "key_events": analysis.key_events,
        }
    except Exception as e:
        logger.error(f"news node failed: {e}")
        return {**state, "error": str(e)}
