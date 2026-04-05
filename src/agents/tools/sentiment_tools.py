"""Sentiment & Escalation Agent tools.

Tools for analyzing sentiment, detecting urgency, and triggering human escalation.
These tools are lightweight — they use heuristics rather than external API calls.
"""

from langchain_core.tools import tool


@tool
def analyze_sentiment(text: str) -> str:
    """Analyze the emotional sentiment of a user message.

    Returns a sentiment score from -1.0 (very negative) to 1.0 (very positive)
    and a classification label.

    Args:
        text: The user message to analyze.
    """
    # Heuristic-based sentiment signals
    text_lower = text.lower()

    negative_signals = [
        "frustrated", "angry", "terrible", "worst", "awful", "hate",
        "furioso", "frustrado", "péssimo", "horrível", "absurdo", "vergonha",
        "ridiculo", "ridículo", "inaceitável", "processando", "processar",
        "procon", "reclamar", "reclame aqui",
    ]
    positive_signals = [
        "thank", "great", "love", "excellent", "perfect", "amazing",
        "obrigado", "obrigada", "ótimo", "excelente", "perfeito", "maravilhoso",
    ]

    # Check for uppercase (shouting indicator)
    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    exclamation_count = text.count("!")

    neg_count = sum(1 for s in negative_signals if s in text_lower)
    pos_count = sum(1 for s in positive_signals if s in text_lower)

    # Compute score
    score = 0.0
    if neg_count > 0:
        score -= 0.3 * neg_count
    if pos_count > 0:
        score += 0.3 * pos_count
    if caps_ratio > 0.5:
        score -= 0.3  # Shouting
    if exclamation_count > 3:
        score -= 0.2  # Excessive punctuation

    score = max(-1.0, min(1.0, score))

    if score <= -0.5:
        label = "frustrated"
    elif score <= -0.2:
        label = "negative"
    elif score <= 0.2:
        label = "neutral"
    else:
        label = "positive"

    return f"Sentiment Score: {score:.2f}, Label: {label}"


@tool
def detect_urgency(text: str) -> str:
    """Classify the urgency level of a support request.

    Returns: low, medium, high, or critical.

    Args:
        text: The user message to classify.
    """
    text_lower = text.lower()

    critical_signals = [
        "lawsuit", "lawyer", "sue", "legal action",
        "processo", "advogado", "processar", "ação judicial",
        "procon", "banco central", "fraude", "fraud",
        "roubo", "stolen", "security breach",
    ]

    high_signals = [
        "urgent", "immediately", "asap", "emergency",
        "urgente", "imediatamente", "emergência",
        "money missing", "dinheiro sumiu", "não consigo acessar",
        "can't access", "blocked", "bloqueado",
    ]

    if any(s in text_lower for s in critical_signals):
        return "Urgency Level: CRITICAL - Immediate human attention required"

    if any(s in text_lower for s in high_signals):
        return "Urgency Level: HIGH - Priority handling needed"

    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    if caps_ratio > 0.6:
        return "Urgency Level: HIGH - Customer appears very agitated (caps lock)"

    return "Urgency Level: MEDIUM - Standard handling"


@tool
def escalate_to_human(user_id: str, reason: str) -> str:
    """Trigger escalation to a human support agent.

    Creates an escalation session, optionally sends a WhatsApp notification
    to the configured operator number, and returns a reference ID.

    Args:
        user_id: The customer's user ID.
        reason: Why this conversation needs human attention.
    """
    from src.infrastructure.whatsapp import client as whatsapp_client
    from src.infrastructure.whatsapp.session_store import session_store
    from src.settings import settings

    operator_number = settings.whatsapp_operator_number or "operator"
    session_id = session_store.create_session(user_id=user_id, operator_number=operator_number)

    # Notify the operator via WhatsApp (no-op when WHATSAPP_ENABLED=false)
    if settings.whatsapp_enabled and operator_number != "operator":
        notification = (
            f"🚨 *ESCALAMENTO — InfinitePay AI*\n\n"
            f"*Sessão:* {session_id}\n"
            f"*Cliente:* {user_id}\n"
            f"*Motivo:* {reason}\n\n"
            f"Responda esta mensagem para interagir diretamente com o cliente no chat."
        )
        whatsapp_client.send_message(operator_number, notification)

    return (
        f"ESCALATION TRIGGERED\n"
        f"Customer: {user_id}\n"
        f"Reason: {reason}\n"
        f"Session: {session_id}\n"
        f"Status: Routed to human agent queue\n"
        f"Estimated wait time: ~5 minutes\n"
        f"Reference: {session_id}"
    )


@tool
def generate_escalation_summary(conversation_context: str) -> str:
    """Generate a brief summary for the human agent receiving the escalation.

    This tool creates a context packet so the human agent can quickly
    understand the situation without reading the full conversation.

    Args:
        conversation_context: Key points from the conversation so far.
    """
    return (
        f"📋 ESCALATION SUMMARY FOR HUMAN AGENT\n"
        f"{'=' * 40}\n"
        f"{conversation_context}\n"
        f"{'=' * 40}\n"
        f"Action Required: Review customer issue and provide personalized resolution.\n"
        f"Priority: High\n"
        f"Note: Customer was previously assisted by AI agent."
    )
