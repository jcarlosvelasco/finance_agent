import json
import logging

from src.graph.state import AnalysisState
from src.langfuse import langfuse
from src.nodes.prompts import JUDGE_PROMPT
from src.shared.llm import get_llm

llm = get_llm()

logger = logging.getLogger(__name__)


async def evaluate_report(state: AnalysisState) -> AnalysisState:
    logger.info("Evaluating report...")

    trace = langfuse.trace(name="evaluate_report_node")

    report = state.get("report")
    if not report:
        return {**state, "evaluation": None}

    company_info = state.get("company_info", {})
    key_events = state.get("key_events", [])

    prompt = JUDGE_PROMPT.format(
        name=company_info.get("name", "N/A"),
        ticker=state.get("ticker", "N/A"),
        price=company_info.get("price", 0),
        market_cap=company_info.get("market_cap", 0),
        sentiment=state.get("sentiment", "N/A"),
        key_events=", ".join(key_events) if key_events else "No events",
        report=report,
    )

    span = trace.span(name="llm_judge", input={"prompt": prompt})

    try:
        response = await llm.ainvoke(prompt)
        content = response.content

        logger.info("LLM judge response: %s", content)

        if isinstance(content, list):
            raise ValueError(f"Expected a string, got a list: {content}")

        clean = content.strip().removeprefix("```json").removesuffix("```").strip()

        logger.info("Cleaned LLM judge response: %s", clean)

        evaluation = json.loads(clean)

        logger.info("Evaluation: %s", evaluation)

        span.end(output=evaluation)

        for metric, score in evaluation["scores"].items():
            langfuse.score(
                trace_id=trace.id,
                name=metric,
                value=score / 5.0,
                comment=evaluation.get("reasoning", ""),
            )

        return {**state, "evaluation": evaluation}

    except Exception as e:
        span.end(output={"error": str(e)})
        return {**state, "evaluation": None, "error": f"Evaluation error: {str(e)}"}
