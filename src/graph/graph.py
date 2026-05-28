from langgraph.graph import END, START, StateGraph

from src.agents.fundamentals import fundamentals
from src.agents.supervisor import supervisor
from src.graph.state import AnalysisState

graph = StateGraph(AnalysisState)
graph.add_node("supervisor", supervisor)
graph.add_edge(START, "supervisor")
graph.add_node("fundamentals", fundamentals)
graph.add_edge("fundamentals", END)
graph.add_edge("supervisor_error", END)


def should_continue_after_supervisor(state: AnalysisState) -> str:
    if state["valid_ticker"]:
        return "fundamentals"
    else:
        return "supervisor_error"


graph.add_conditional_edges(
    "supervisor",
    should_continue_after_supervisor,
    ["fundamentals", "supervisor_error"],
)
