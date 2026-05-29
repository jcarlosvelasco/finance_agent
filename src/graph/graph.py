from langgraph.graph import END, START, StateGraph

from src.graph.state import AnalysisState
from src.nodes.fundamentals import fundamentals
from src.nodes.news import news
from src.nodes.report import report
from src.nodes.supervisor import supervisor

graph = StateGraph(AnalysisState)

graph.add_node("supervisor", supervisor)
graph.add_node("fundamentals", fundamentals)
graph.add_node("news", news)
graph.add_node("report", report)

graph.add_edge(START, "supervisor")
graph.add_edge("report", END)


def should_continue_after_supervisor(state: AnalysisState) -> str:
    if state["valid_ticker"]:
        return "fundamentals"

    return END


def should_continue_after_fundamentals(state: AnalysisState) -> str:
    if state["company_info"]:
        return "news"

    return END


def should_continue_after_news(state: AnalysisState) -> str:
    if state.get("sentiment") and state.get("key_events"):
        return "report"

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
