import logging

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.graph.state import AnalysisState
from src.nodes.evaluate_report import evaluate_report
from src.nodes.fundamentals import fundamentals
from src.nodes.news import news
from src.nodes.report import report
from src.nodes.save_report import save_report
from src.nodes.supervisor import supervisor

logger = logging.getLogger(__name__)

graph = StateGraph(AnalysisState)

graph.add_node("supervisor", supervisor)
graph.add_node("fundamentals", fundamentals)
graph.add_node("news", news)
graph.add_node("report", report)
graph.add_node("save", save_report)
graph.add_node("evaluate", evaluate_report)

graph.add_edge(START, "supervisor")
graph.add_edge("save", "evaluate")
graph.add_edge("evaluate", END)


def should_continue_after_report(state: AnalysisState) -> str:
    logger.info(
        "Report: checking state: report=%s, error=%s", state["report"], state["error"]
    )
    if state["report"] and not state["error"]:
        logger.info("Report: generated, continuing to save")
        return "save"

    logger.warning("Report: no report or error, ending")
    return END


def should_continue_after_supervisor(state: AnalysisState) -> str:
    if state["valid_ticker"] and not state["error"]:
        logger.info("Supervisor: valid ticker, continuing to fundamentals")
        return "fundamentals"

    logger.warning("Supervisor: invalid ticker or error, ending")
    return END


def should_continue_after_fundamentals(state: AnalysisState) -> str:
    if state["company_info"] and not state["error"]:
        logger.info("Fundamentals: company info available, continuing to news")
        return "news"

    logger.warning("Fundamentals: no company info or error, ending")
    return END


def should_continue_after_news(state: AnalysisState) -> str:
    if state.get("sentiment") and state.get("key_events") and not state["error"]:
        logger.info("News: sentiment and key events available, continuing to report")
        return "report"

    logger.warning("News: no sentiment or key events or error, ending")
    return END


graph.add_conditional_edges(
    "supervisor",
    should_continue_after_supervisor,
    {
        "fundamentals": "fundamentals",
    },
)

graph.add_conditional_edges(
    "fundamentals",
    should_continue_after_fundamentals,
    {
        "news": "news",
        END: END,
    },
)

graph.add_conditional_edges(
    "news",
    should_continue_after_news,
    {
        "report": "report",
        END: END,
    },
)

graph.add_conditional_edges(
    "report",
    should_continue_after_report,
    {
        "save": "save",
        END: END,
    },
)

checkpointer = MemorySaver()
compiled_app = graph.compile(checkpointer=checkpointer)
