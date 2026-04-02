"""LangGraph StateGraph — The Agent Swarm.

This is the central orchestration module. It assembles all agents, guardrails,
and routing logic into a single compiled LangGraph StateGraph.
"""

from __future__ import annotations

import logging
from typing import Literal

from langgraph.graph import END, START, StateGraph

from src.agents.guardrails.input_guard import input_guard_node
from src.agents.guardrails.output_guard import output_guard_node
from src.agents.nodes.knowledge_node import create_knowledge_node
from src.agents.nodes.router_node import router_node
from src.agents.nodes.sentiment_node import sentiment_node
from src.agents.nodes.support_node import create_support_node
from src.agents.state import AgentState
from src.domain.ports.knowledge_store import KnowledgeStore
from src.domain.ports.ticket_repository import TicketRepository
from src.domain.ports.user_repository import UserRepository
from src.domain.ports.web_searcher import WebSearcher

logger = logging.getLogger(__name__)


def _should_continue_after_guard(state: AgentState) -> Literal["router", "__end__"]:
    """After input guard, either continue to router or end if blocked."""
    if state.get("guardrail_blocked", False):
        return "__end__"
    return "router"


def _route_by_intent(
    state: AgentState,
) -> Literal["knowledge", "support", "sentiment"]:
    """Route to the appropriate agent based on classified intent."""
    route = state.get("agent_route", "knowledge")

    route_map = {
        "knowledge": "knowledge",
        "general": "knowledge",
        "support": "support",
        "escalation": "sentiment",
    }

    return route_map.get(route, "knowledge")


def build_swarm(
    knowledge_store: KnowledgeStore,
    web_searcher: WebSearcher,
    user_repo: UserRepository,
    ticket_repo: TicketRepository,
) -> StateGraph:
    """Build and compile the agent swarm StateGraph.

    All dependencies are injected via constructor parameters,
    following the Dependency Inversion Principle.

    Args:
        knowledge_store: Vector store for RAG retrieval.
        web_searcher: Web search engine.
        user_repo: User data repository.
        ticket_repo: Support ticket repository.

    Returns:
        A compiled LangGraph StateGraph ready to invoke.
    """
    # Create agent nodes with injected dependencies
    knowledge_node = create_knowledge_node(knowledge_store, web_searcher)
    support_node = create_support_node(user_repo, ticket_repo)

    # Build the graph
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("input_guard", input_guard_node)
    graph.add_node("router", router_node)
    graph.add_node("knowledge", knowledge_node)
    graph.add_node("support", support_node)
    graph.add_node("sentiment", sentiment_node)
    graph.add_node("output_guard", output_guard_node)

    # Add edges
    graph.add_edge(START, "input_guard")

    # After input guard: continue or stop
    graph.add_conditional_edges(
        "input_guard",
        _should_continue_after_guard,
        {
            "router": "router",
            "__end__": END,
        },
    )

    # After router: route to specialized agent
    graph.add_conditional_edges(
        "router",
        _route_by_intent,
        {
            "knowledge": "knowledge",
            "support": "support",
            "sentiment": "sentiment",
        },
    )

    # All agents flow to output guard
    graph.add_edge("knowledge", "output_guard")
    graph.add_edge("support", "output_guard")
    graph.add_edge("sentiment", "output_guard")

    # Output guard → END
    graph.add_edge("output_guard", END)

    logger.info("Agent swarm graph built successfully")

    return graph.compile()
