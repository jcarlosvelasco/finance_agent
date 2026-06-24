import json
import logging
import os
import re

from langchain_core.messages import HumanMessage
from langfuse.client import StatefulSpanClient
from tavily import TavilyClient

from src.graph.state import AnalysisState
from src.langfuse import langfuse
from src.nodes.prompts import SENTIMENT_PROMPT
from src.shared.llm import SentimentResponse, get_llm

tavily_api_key = os.getenv("TAVILY_API_KEY")


tavily = TavilyClient(api_key=tavily_api_key)
logger = logging.getLogger(__name__)

llm = get_llm()


def extract_json(text: str) -> dict:
    text = text.strip()

    text = re.sub(r"```json|```", "", text).strip()

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
    raise ValueError(f"No valid JSON found in response: {text}")


async def news(state: AnalysisState) -> dict:
    trace = langfuse.trace(name="news_node")
    span: StatefulSpanClient | None = None

    try:
        span = trace.span(
            name="tavily_search",
            input={
                "query": f"{state.ticker} stock news"
            },
        )

        results = tavily.search(
            query=f"{state.ticker} stock news",
            max_results=8,
            topic="news",
        )

        span.end(output=results)

        headlines = [r["title"] for r in results["results"]]

        span = trace.span(
            name="llm_sentiment_raw",
            input={
                "company": state.ticker,
                "headlines": "\n".join(headlines),
            },
        )

        response = await llm.ainvoke(
            [
                HumanMessage(
                    content=SENTIMENT_PROMPT.format(
                        company=state.ticker,
                        headlines="\n".join(headlines),
                    )
                )
            ]
        )

        span.end(output=response.content)

        span = trace.span(
            name="llm_sentiment_parsed",
            input={"data": response.content},
        )

        if isinstance(response.content, str):
            data = extract_json(response.content)
        elif isinstance(response.content, dict):
            data = response.content
        elif isinstance(response.content, list):
            text_block = next(
                (
                    item["text"] if isinstance(item, dict) else item
                    for item in response.content
                    if isinstance(item, dict)
                    and item.get("type") == "text"
                    or isinstance(item, str)
                ),
                None,
            )
            if text_block is None:
                raise ValueError(
                    f"No text content found in response: {response.content}"
                )
            data = extract_json(text_block)
        else:
            raise ValueError(
                f"Unexpected response content type: {type(response.content)}"
            )

        span.end(output=data)

        analysis = SentimentResponse.model_validate(data)

        return {
            "news_items": results["results"],
            "sentiment": analysis.sentiment,
            "key_events": analysis.key_events,
        }

    except Exception as e:
        logger.error(f"news node failed: {e}")

        trace.update(
            metadata={
                "error": str(e),
                "status": "failed",
                "ticker": state.ticker,
            }
        )

        try:
            if span is not None:
                span.end(output={"error": str(e)})
        except Exception:
            pass

        return {"error": str(e)}
