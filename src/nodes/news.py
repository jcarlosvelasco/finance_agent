import json
import os

from tavily import TavilyClient

from src.graph.state import AnalysisState
from src.nodes.prompts import SENTIMENT_PROMPT
from src.shared.llm import get_llm

tavily_api_key = os.getenv("TAVILY_API_KEY")


tavily = TavilyClient(api_key=tavily_api_key)
llm = get_llm()


async def news(state: AnalysisState) -> AnalysisState:
    try:
        results = tavily.search(
            query=f"{state['ticker']} {state.get('company_name', '')} stock news",
            max_results=8,
            topic="news",
        )
        headlines = [r["title"] for r in results["results"]]

        response = await llm.ainvoke(
            SENTIMENT_PROMPT.format(
                company=state.get("company_name", state["ticker"]),
                headlines="\n".join(headlines),
            )
        )

        content = response.content

        if isinstance(content, list):
            content = "".join(
                item if isinstance(item, str) else str(item) for item in content
            )

        analysis = json.loads(content)

        return {
            **state,
            "news_items": results["results"],
            "sentiment": analysis["sentiment"],
            "key_events": analysis["key_events"],
        }
    except Exception as e:
        return {**state, "error": str(e)}
