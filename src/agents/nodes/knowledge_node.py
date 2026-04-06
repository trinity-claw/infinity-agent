"""Knowledge Agent node.

Handles product questions via RAG and general questions via web search.
Uses tool-calling with LangGraph's prebuilt ToolNode pattern.
"""

from __future__ import annotations

import logging
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from src.agents.prompts.knowledge_prompt import KNOWLEDGE_SYSTEM_PROMPT
from src.agents.routing_rules import is_support_overlap_query
from src.agents.state import AgentState
from src.agents.tools.knowledge_tools import create_knowledge_tools
from src.domain.ports.knowledge_store import KnowledgeStore
from src.domain.ports.web_searcher import WebSearcher
from src.infrastructure.llm.model_factory import get_knowledge_llm

logger = logging.getLogger(__name__)


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
    """Backward-compatible local wrapper around shared routing rules."""
    return is_support_overlap_query(message)


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
        "Essa solicitação parece um problema operacional de suporte, e não uma dúvida de base de "
        "conhecimento. Por favor, siga pelo fluxo de suporte/atendente humano para verificarmos "
        "diagnóstico em tempo real."
    )


def _format_web_results_for_prompt(web_results: list) -> str:
    """Format web search results for synthesis prompt."""
    return "\n\n".join(
        [
            f"{idx}. {item.title}\n{item.snippet}\nURL: {item.url}"
            for idx, item in enumerate(web_results, start=1)
        ]
    )


def _build_web_synthesis_prompt(formatted_results: str) -> str:
    """Prompt for deterministic web-answer synthesis."""
    return (
        "Você é um agente de resposta baseado em resultados de busca web.\n"
        "Use SOMENTE os resultados abaixo.\n"
        "Regras:\n"
        "1) Responda em português do Brasil.\n"
        "2) Não repita a pergunta do usuário.\n"
        "3) Traga um resumo direto e, quando fizer sentido, bullets com os destaques.\n"
        "4) Cite 3 a 5 fontes com URL ao final.\n"
        "5) Se a pergunta for sobre 'hoje', deixe claro que o cenário "
        "pode mudar ao longo do dia.\n\n"
        + f"Resultados web:\n{formatted_results}"
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

        # Deterministic web path for non-InfinitePay/general queries.
        # This avoids low-value tool-calling misses and echo responses.
        if user_message and not _is_infinitepay_query(user_message):
            logger.info(
                "Knowledge deterministic web-search path message=%s",
                user_message[:120],
            )
            web_results = await web_searcher.search(user_message, max_results=6)
            if web_results:
                formatted = _format_web_results_for_prompt(web_results)
                synthesis_prompt = _build_web_synthesis_prompt(formatted)
                synthesized = await get_knowledge_llm().ainvoke(
                    [
                        SystemMessage(content=synthesis_prompt),
                        HumanMessage(content=user_message),
                    ]
                )
                synthesized_text = str(synthesized.content or "").strip()
                if _looks_like_echo_response(user_message, synthesized_text):
                    synthesized_text = (
                        "Encontrei resultados na web, mas não consegui "
                        "montar uma resposta confiável. "
                        "Tente reformular sua pergunta com mais contexto."
                    )

                return {
                    "messages": [
                        AIMessage(
                            content=synthesized_text,
                            name="knowledge",
                        )
                    ],
                    "metadata": {
                        **state.get("metadata", {}),
                        "knowledge_deterministic_web_search": True,
                        "knowledge_web_results_count": len(web_results),
                    },
                }

            return {
                "messages": [
                    AIMessage(
                        content=(
                            "Não consegui recuperar fontes web confiáveis agora. "
                            "Tente novamente em instantes ou reformule a pergunta."
                        ),
                        name="knowledge",
                    )
                ],
                "metadata": {
                    **state.get("metadata", {}),
                    "knowledge_deterministic_web_search": True,
                    "knowledge_web_search_empty": True,
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

        response = None
        for _ in range(3):
            response = await llm.ainvoke(messages)
            if not response.tool_calls:
                break

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

            messages = messages + [response] + tool_results

        # No (remaining) tool calls - LLM answered directly.
        return {
            "messages": [
                AIMessage(content=response.content, name="knowledge")
            ],
        }

    return knowledge_node
