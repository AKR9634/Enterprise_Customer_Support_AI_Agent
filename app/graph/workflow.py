"""
Builds and compiles the LangGraph state graph: wires the 8 nodes
together in order (classify -> context -> retrieve -> business_data
-> route -> generate -> verify -> decide) and exposes run_graph().
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from app.graph.nodes.business_data import BusinessDataNode
from app.graph.nodes.classify import ClassifyNode
from app.graph.nodes.context import ContextNode
from app.graph.nodes.decide import DecideNode
from app.graph.nodes.generate import GenerateNode
from app.graph.nodes.retrieve import RetrieveNode
from app.graph.nodes.verify import VerifyNode
from app.graph.state import SupportState
from app.llm.provider import LLMClient

__all__ = [
    "build_graph",
    "run_graph",
]


def build_graph(
    llm: LLMClient | None = None,
    conn: Any | None = None,
) -> StateGraph:
    """Construct the LangGraph state graph.

    Phase 3 wiring — Nodes 1-3 and 6-8 are wired linearly.
    Nodes 4 (business_data) and 5 (route) are Phase 4 and remain
    omitted until their implementation steps.
    """
    classify = ClassifyNode(llm=llm)
    context = ContextNode(conn=conn)  # type: ignore[arg-type]
    retrieve = RetrieveNode()
    business_data = BusinessDataNode(conn=conn)  # type: ignore[arg-type]
    generate = GenerateNode(llm=llm)
    verify = VerifyNode(llm=llm)
    decide = DecideNode()

    builder = StateGraph(SupportState)

    builder.add_node("classify", classify)
    builder.add_node("context", context)
    builder.add_node("retrieve", retrieve)
    builder.add_node("business_data", business_data)
    builder.add_node("generate", generate)
    builder.add_node("verify", verify)
    builder.add_node("decide", decide)

    builder.set_entry_point("classify")
    builder.add_edge("classify", "context")
    builder.add_edge("context", "retrieve")
    builder.add_edge("retrieve", "business_data")
    builder.add_edge("business_data", "generate")
    builder.add_edge("generate", "verify")
    builder.add_edge("verify", "decide")
    builder.add_edge("decide", END)

    return builder


def run_graph(
    initial_state: SupportState,
    *,
    llm: LLMClient | None = None,
    conn: Any | None = None,
) -> dict[str, Any]:
    """Compile the graph, run it with *initial_state*, and return the
    final state dict.

    Convenience wrapper around ``build_graph(…)`` for external callers
    that don't need to keep a reference to the compiled graph.
    """
    builder = build_graph(llm=llm, conn=conn)
    graph = builder.compile()
    result = graph.invoke(initial_state)
    return result
