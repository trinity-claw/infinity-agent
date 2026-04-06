"""Knowledge Agent node.

Handles product questions via RAG and general questions via web search.
Uses tool-calling with LangGraph's prebuilt ToolNode pattern.
"""

from __future__ import annotations

import logging
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from src.agents.prompts.knowledge_prompt import KNOWLEDGE_SYSTEM_PROMPT
from src.agents.state import AgentState
from src.agents.tools.knowledge_tools import create_knowledge_tools
from src.domain.ports.knowledge_store import KnowledgeStore
from src.domain.ports.web_searcher import WebSearcher
from src.infrastructure.llm.model_factory import get_knowledge_llm

logger = logging.getLogger(__name__)


_SUPPORT_OVERLAP_PATTERNS = (
    r"\bstatus\b.{0,25}\bservic",
    r"\bservice status\b",
    r"\b(outage|downtime|instab|indispon|fora do ar|is down)\b",
    r"\b(infinitepay|service|servico|servicos)\b.{0,20}\bdown\b",
    r"\bnao consigo\b.{0,30}\b(acessar|entrar|transferir|pagar)\b",
    r"\bi can't\b.{0,30}\b(sign in|login|transfer|pay)\b",
)

_INFINITEPAY_PATTERNS = (
    r"\binfinitepay\b",
    r"\bmaquininha\b",
    r"\binfinitetap\b",
    r"\bpix\b",
    r"\blink de pagamento\b",
    r"\bconta digital\b",
    r"\bconta pj\b",
    r"\bcartao\b",
    r"\bemprestimo\b",
    r"\brendimento\b",
    r"\bpdv\b",
    r"\bbolet[oa]\b",
    r"\btaxa(s)?\b",
)


def _is_support_overlap_query(message: str) -> bool:
    """Detect support-style operational issues that were misrouted to knowledge."""
    if not message:
        return False
    text = message.lower()
    return any(re.search(pattern, text) for pattern in _SUPPORT_OVERLAP_PATTERNS)


def _is_infinitepay_query(message: str) -> bool:
    """Detect likely InfinitePay/domain queries."""
    if not message:
        return False
    text = message.lower()
    return any(re.search(pattern, text) for pattern in _INFINITEPAY_PATTERNS)


def _looks_like_echo_response(user_message: str, llm_response: str) -> bool:
    """Detect low-value response patterns (e.g., plain echo)."""
    if not llm_response:
        return True
    normalized_user = re.sub(r"\s+", " ", user_message.strip().lower())
    normalized_llm = re.sub(r"\s+", " ", llm_response.strip().lower())
    return normalized_llm == normalized_user


def _build_support_overlap_message(message: str) -> str:
    """Build a safer response for operational/support questions."""
    lower = (message or "").lower()
    if any(
        token in lower
        for token in ("is down", "service status", "outage", "downtime", "can't", "cannot")
    ):
        return (
            "This request looks like an operational support issue, not a knowledge-base topic. "
            "Please continue through support/human handoff so we can check real-time "
            "service diagnostics."
        )
    return (
        "Essa solicitacao parece um problema operacional de suporte, e nao uma duvida de base de "
        "conhecimento. Por favor, siga pelo fluxo de suporte/atendente humano para verificarmos "
        "diagnostico em tempo real."
    )


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

        The LLM decides which tool to use based on question type:
        - InfinitePay questions -> search_knowledge_base
        - General questions -> search_web
        """
        user_message = ""
        for msg in reversed(state["messages"]):
            if getattr(msg, "type", "") == "human":
                user_message = getattr(msg, "content", "") or ""
                break

        if _is_support_overlap_query(user_message):
            logger.info(
                "Knowledge overlap fallback triggered for support-style message=%s",
                user_message[:120],
            )
            return {
                "messages": [
                    AIMessage(
                        content=_build_support_overlap_message(user_message),
                        name="knowledge",
                    )
                ],
                "metadata": {
                    **state.get("metadata", {}),
                    "knowledge_overlap_fallback": True,
                },
            }

        llm = get_knowledge_llm().bind_tools(tools)
        authenticated_user = state.get("metadata", {}).get("authenticated_user", {})
        auth_name = authenticated_user.get("name", "")
        auth_email = authenticated_user.get("email", "")

        profile_lines = []
        if auth_name:
            profile_lines.append(f"- Authenticated name: {auth_name}")
        if auth_email:
            profile_lines.append(f"- Authenticated email: {auth_email}")

        profile_block = (
            "\n".join(profile_lines)
            if profile_lines
            else "- No authenticated profile provided."
        )
        context_prompt = (
            f"{KNOWLEDGE_SYSTEM_PROMPT}\n\n"
            f"## Session Context\n"
            f"{profile_block}\n"
            f"If authenticated name is available and it sounds natural, personalize the greeting."
        )
        messages = [SystemMessage(content=context_prompt)] + list(state["messages"])

        # First call: LLM decides which tool(s) to use.
        response = await llm.ainvoke(messages)

        # If tool calls are present, execute them.
        if response.tool_calls:
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

            # Second call: LLM synthesizes final response using tool results.
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

        # No tool calls - force web search for out-of-domain/general questions.
        if (
            user_message
            and not _is_infinitepay_query(user_message)
            and _looks_like_echo_response(user_message, str(response.content or ""))
        ):
            logger.info(
                "Knowledge forced web-search fallback (echo/no-tool) message=%s",
                user_message[:120],
            )
            web_results = await web_searcher.search(user_message, max_results=5)
            if web_results:
                formatted = "\n\n".join(
                    [
                        f"{idx}. {item.title}\n{item.snippet}\nURL: {item.url}"
                        for idx, item in enumerate(web_results, start=1)
                    ]
                )
                synthesis_prompt = (
                    "Use only the web results below to answer the user. "
                    "Be concise, mention that the information comes from web sources, "
                    "and include the URLs when useful.\n\n"
                    f"Web results:\n{formatted}"
                )
                forced_response = await get_knowledge_llm().ainvoke(
                    [
                        SystemMessage(content=synthesis_prompt),
                        HumanMessage(content=user_message),
                    ]
                )
                return {
                    "messages": [
                        AIMessage(
                            content=str(forced_response.content or "").strip(),
                            name="knowledge",
                        )
                    ],
                    "metadata": {
                        **state.get("metadata", {}),
                        "knowledge_forced_web_search": True,
                    },
                }

            return {
                "messages": [
                    AIMessage(
                        content=(
                            "Nao consegui recuperar fontes web confiaveis agora. "
                            "Tente reformular a pergunta ou tente novamente em instantes."
                        ),
                        name="knowledge",
                    )
                ],
                "metadata": {
                    **state.get("metadata", {}),
                    "knowledge_forced_web_search": True,
                    "knowledge_web_search_empty": True,
                },
            }

        # No tool calls - LLM answered directly.
        return {
            "messages": [
                AIMessage(content=response.content, name="knowledge")
            ],
        }

    return knowledge_node
