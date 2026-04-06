"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    openrouter_api_key: str = ""

    router_model: str = "openai/gpt-4o-mini"
    knowledge_model: str = "google/gemini-2.5-flash"
    support_model: str = "anthropic/claude-sonnet-4.5"
    sentiment_model: str = "openai/gpt-4o-mini"
    guardrail_model: str = "openai/gpt-4o-mini"

    embedding_model: str = "openai/text-embedding-3-small"

    brave_search_api_key: str = ""
    brave_search_base_url: str = "https://api.search.brave.com/res/v1/web/search"

    chroma_persist_dir: str = "./data/chroma_db"

    sqlite_db_path: str = "./data/langgraph.sqlite"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    cors_allow_origins: str = "*"

    enable_guardrails: bool = True
    enable_streaming: bool = True
    enable_sentiment_agent: bool = True

    whatsapp_enabled: bool = False
    whatsapp_api_url: str = ""
    whatsapp_api_token: str = ""
    whatsapp_instance: str = "main"
    whatsapp_operator_number: str = ""

    # Sensitive endpoint authentication (enforced only in production)
    sensitive_api_key: str = ""

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() == "production"


settings = Settings()
