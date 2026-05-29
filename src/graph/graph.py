from langgraph.graph import END, START, StateGraph

from src.graph.state import AnalysisState
from src.nodes.fundamentals import fundamentals
from src.nodes.news import news
from src.nodes.supervisor import supervisor

graph = StateGraph(AnalysisState)

graph.add_node("supervisor", supervisor)
graph.add_node("fundamentals", fundamentals)
graph.add_node("news", news)

graph.add_edge(START, "supervisor")
graph.add_edge("fundamentals", END)
graph.add_edge("news", END)


def should_continue_after_supervisor(state: AnalysisState) -> str:
    if state["valid_ticker"]:
        return "fundamentals"

    return END


def should_continue_after_fundamentals(state: AnalysisState) -> str:
    if state["company_info"]:
        return "news"

    return END


graph.add_conditional_edges(
    "supervisor",
    should_continue_after_supervisor,
    {
        "fundamentals": "fundamentals",
        "news": "news",
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
