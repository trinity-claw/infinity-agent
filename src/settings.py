"""Application settings loaded from environment variables.

Uses Pydantic Settings for type-safe configuration with .env file support.
All sensitive values come from environment; defaults are safe for development.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- OpenRouter ---
    openrouter_api_key: str = ""

    # --- LLM Models (OpenRouter model IDs) ---
    router_model: str = "openai/gpt-4o-mini"
    knowledge_model: str = "openai/gpt-4o-mini"
    support_model: str = "anthropic/claude-sonnet-4.5"
    sentiment_model: str = "openai/gpt-4o-mini"
    guardrail_model: str = "openai/gpt-4o-mini"

    # --- Embeddings ---
    embedding_model: str = "openai/text-embedding-3-small"

    # --- ChromaDB ---
    chroma_persist_dir: str = "./data/chroma_db"

    # --- Application ---
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # --- Feature Flags ---
    enable_guardrails: bool = True
    enable_streaming: bool = True
    enable_sentiment_agent: bool = True

    # --- WhatsApp Escalation ---
    whatsapp_enabled: bool = False
    whatsapp_api_url: str = ""           # e.g. https://your-evolution-api-host
    whatsapp_api_token: str = ""         # Evolution API: apikey header
    whatsapp_instance: str = "main"      # Evolution API instance name
    whatsapp_operator_number: str = ""   # E.164 digits only: 5511999999999

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


# Singleton instance — import this everywhere
settings = Settings()
