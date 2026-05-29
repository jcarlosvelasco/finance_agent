import json

from tavily import TavilyClient

from src.graph.state import AnalysisState
from src.shared.llm import get_llm

tavily = TavilyClient()
llm = get_llm()

SENTIMENT_PROMPT = """Analyze the sentiment of these news headlines about {company}.
Classify as: positive | negative | neutral | mixed.
Also identify the top 3 most significant events mentioned.

Headlines:
{headlines}

Respond with JSON:
{{"sentiment": "...", "key_events": ["...", "...", "..."]}}"""


async def run(state: AnalysisState) -> AnalysisState:
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

        analysis = json.loads(response.content)

        return {
            "news_items": results["results"],
            "sentiment": analysis["sentiment"],
            "key_events": analysis["key_events"],
        }
    except Exception as e:
        return {"errors": [f"news_agent failed: {e}"]}
