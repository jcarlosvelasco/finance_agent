from langgraph.graph import END, START, StateGraph

from src.agents.fundamentals import fundamentals
from src.agents.supervisor import supervisor
from src.graph.state import AnalysisState

graph = StateGraph(AnalysisState)

graph.add_node("supervisor", supervisor)
graph.add_node("fundamentals", fundamentals)

graph.add_edge(START, "supervisor")
graph.add_edge("fundamentals", END)


def should_continue_after_supervisor(state: AnalysisState) -> str:
    if state["valid_ticker"]:
        return "fundamentals"

    return END


graph.add_conditional_edges(
    "supervisor",
    should_continue_after_supervisor,
    {
        "fundamentals": "fundamentals",
        END: END,
    },
)
