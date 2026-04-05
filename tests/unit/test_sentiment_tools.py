"""Unit tests for Sentiment & Escalation Agent tools."""

import pytest

from src.agents.tools.sentiment_tools import (
    analyze_sentiment,
    detect_urgency,
    escalate_to_human,
    generate_escalation_summary,
)


class TestAnalyzeSentiment:
    def test_positive_message(self):
        result = analyze_sentiment.invoke({"text": "Obrigado, vocês são excelentes! Atendimento perfeito."})
        assert "positive" in result.lower()
        assert "0." in result  # score present

    def test_negative_message(self):
        result = analyze_sentiment.invoke({"text": "Estou furioso com esse péssimo serviço absurdo!"})
        assert any(word in result.lower() for word in ["frustrated", "negative"])

    def test_neutral_message(self):
        result = analyze_sentiment.invoke({"text": "Quero saber sobre o Pix."})
        assert "neutral" in result.lower()

    def test_caps_lock_detected_as_negative(self):
        result = analyze_sentiment.invoke({"text": "QUERO MINHA GRANA DE VOLTA AGORA"})
        assert any(word in result.lower() for word in ["frustrated", "negative", "high"])

    def test_score_in_range(self):
        for text in ["ótimo", "péssimo", "ok"]:
            result = analyze_sentiment.invoke({"text": text})
            # Extract score value
            parts = result.split("Score: ")
            if len(parts) > 1:
                score_str = parts[1].split(",")[0]
                score = float(score_str)
                assert -1.0 <= score <= 1.0


class TestDetectUrgency:
    def test_critical_legal_threat(self):
        result = detect_urgency.invoke({"text": "Vou processar a InfinitePay na justiça!"})
        assert "CRITICAL" in result

    def test_critical_fraud(self):
        result = detect_urgency.invoke({"text": "Houve uma fraude na minha conta!"})
        assert "CRITICAL" in result

    def test_high_urgency_blocked(self):
        result = detect_urgency.invoke({"text": "Minha conta foi bloqueada urgente!"})
        assert "HIGH" in result or "CRITICAL" in result

    def test_medium_urgency_default(self):
        result = detect_urgency.invoke({"text": "Quero saber sobre minha conta."})
        assert "MEDIUM" in result

    def test_procon_triggers_critical(self):
        result = detect_urgency.invoke({"text": "Vou registrar reclamação no Procon."})
        assert "CRITICAL" in result


class TestEscalateToHuman:
    def test_returns_escalation_trigger(self):
        result = escalate_to_human.invoke({"user_id": "client789", "reason": "Cliente muito frustrado"})
        assert "ESCALATION TRIGGERED" in result
        assert "client789" in result

    def test_includes_reference_number(self):
        result = escalate_to_human.invoke({"user_id": "client001", "reason": "Fraude reportada"})
        assert "ESC-" in result

    def test_includes_wait_time(self):
        result = escalate_to_human.invoke({"user_id": "user123", "reason": "Processo judicial"})
        assert "minutos" in result or "minute" in result


class TestGenerateEscalationSummary:
    def test_returns_summary_header(self):
        result = generate_escalation_summary.invoke({"conversation_context": "Cliente perdeu R$ 500"})
        assert "ESCALATION SUMMARY" in result

    def test_includes_context(self):
        context = "Cliente relatou cobrança duplicada de R$ 200"
        result = generate_escalation_summary.invoke({"conversation_context": context})
        assert context in result
