"""Tests for knowledge-node web fallback heuristics."""

from __future__ import annotations

from src.agents.nodes import knowledge_node as knowledge_module


def test_detect_infinitepay_domain_query() -> None:
    assert knowledge_module._is_infinitepay_query("Quais as taxas da maquininha?") is True
    assert knowledge_module._is_infinitepay_query("Como funciona o InfiniteTap?") is True


def test_detect_non_infinitepay_query() -> None:
    assert knowledge_module._is_infinitepay_query("Quais as principais noticias de Sao Paulo hoje?") is False


def test_detect_echo_response() -> None:
    user = "Quais as principais noticias de Sao Paulo hoje?"
    llm = "Quais as principais noticias de Sao Paulo hoje?"
    assert knowledge_module._looks_like_echo_response(user, llm) is True


def test_detect_non_echo_response() -> None:
    user = "Quais as principais noticias de Sao Paulo hoje?"
    llm = "Aqui estao os destaques de hoje em Sao Paulo com fontes externas."
    assert knowledge_module._looks_like_echo_response(user, llm) is False
