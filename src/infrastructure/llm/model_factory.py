"""LLM Model Factory.

Creates ChatOpenRouter instances for each agent role.
Centralizes model configuration so agent nodes stay clean.
LLM instances are created lazily (at call time, not at import time).
"""

from __future__ import annotations

from langchain_openrouter import ChatOpenRouter

from src.settings import settings


def create_llm(
    model: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> ChatOpenRouter:
    """Create a ChatOpenRouter LLM instance.

    Args:
        model: OpenRouter model ID (e.g., 'openai/gpt-4o-mini').
               Defaults to the router model from settings.
        temperature: Sampling temperature. Lower = more deterministic.
        max_tokens: Maximum tokens in the response.

    Returns:
        A configured ChatOpenRouter instance.

    Raises:
        ValueError: If OPENROUTER_API_KEY is not configured.
    """
    api_key = settings.openrouter_api_key
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not set. "
            "Create a .env file with your OpenRouter API key. "
            "See .env.example for the template."
        )

    return ChatOpenRouter(
        model=model or settings.router_model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def get_router_llm() -> ChatOpenRouter:
    """LLM for the Router Agent — fast classification."""
    return create_llm(model=settings.router_model, temperature=0.0, max_tokens=512)


def get_knowledge_llm() -> ChatOpenRouter:
    """LLM for the Knowledge Agent — RAG generation."""
    return create_llm(model=settings.knowledge_model, temperature=0.2, max_tokens=2048)


def get_support_llm() -> ChatOpenRouter:
    """LLM for the Support Agent — empathetic, nuanced responses."""
    return create_llm(model=settings.support_model, temperature=0.3, max_tokens=2048)


def get_sentiment_llm() -> ChatOpenRouter:
    """LLM for the Sentiment Agent — sentiment classification."""
    return create_llm(model=settings.sentiment_model, temperature=0.0, max_tokens=512)


def get_guardrail_llm() -> ChatOpenRouter:
    """LLM for guardrail evaluation."""
    return create_llm(model=settings.guardrail_model, temperature=0.0, max_tokens=256)
