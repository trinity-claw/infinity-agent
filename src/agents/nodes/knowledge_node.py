"""Knowledge Agent node.

Handles product questions via RAG and general questions via web search.
Uses tool-calling with LangGraph's prebuilt ToolNode pattern.
"""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage, SystemMessage

from src.agents.prompts.knowledge_prompt import KNOWLEDGE_SYSTEM_PROMPT
from src.agents.state import AgentState
from src.agents.tools.knowledge_tools import create_knowledge_tools
from src.domain.ports.knowledge_store import KnowledgeStore
from src.domain.ports.web_searcher import WebSearcher
from src.infrastructure.llm.model_factory import get_knowledge_llm

logger = logging.getLogger(__name__)


def create_knowledge_node(
    knowledge_store: KnowledgeStore,
    web_searcher: WebSearcher,
):
    """Factory that creates a knowledge node with injected dependencies.

    Args:
        knowledge_store: Vector store for RAG retrieval.
        web_searcher: Web search engine for general questions.

    Returns:
        An async function that serves as the LangGraph node.
    """
    tools = create_knowledge_tools(knowledge_store, web_searcher)

    async def knowledge_node(state: AgentState) -> dict:
        """Process knowledge/general questions using RAG or web search.

        The LLM decides which tool to use based on the question type:
        - InfinitePay questions → search_knowledge_base
        - General questions → search_web
        """
        llm = get_knowledge_llm().bind_tools(tools)
        messages = [SystemMessage(content=KNOWLEDGE_SYSTEM_PROMPT)] + list(
            state["messages"]
        )

        # First call: LLM decides which tool(s) to use
        response = await llm.ainvoke(messages)

        # If tool calls are present, execute them
        if response.tool_calls:
            from langchain_core.messages import ToolMessage

            tool_map = {t.name: t for t in tools}
            tool_results = []

            for tool_call in response.tool_calls:
                tool_fn = tool_map.get(tool_call["name"])
                if tool_fn:
                    logger.info("Knowledge agent calling tool: %s", tool_call["name"])
                    result = await tool_fn.ainvoke(tool_call["args"])
                    tool_results.append(
                        ToolMessage(
                            content=str(result),
                            tool_call_id=tool_call["id"],
                        )
                    )

            # Second call: LLM synthesizes the final response using tool results
            messages_with_tools = messages + [response] + tool_results
            final_response = await llm.ainvoke(messages_with_tools)

            return {
                "messages": [
                    AIMessage(
                        content=final_response.content,
                        name="knowledge",
                    )
                ],
            }

        # No tool calls — LLM answered directly
        return {
            "messages": [
                AIMessage(content=response.content, name="knowledge")
            ],
        }

    return knowledge_node
