from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    PROJECT_NAME: str = "Text-to-SQL Clarification Engine API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = (
        "Enterprise-grade Text-to-SQL API featuring dynamic schema discovery, "
        "interactive ambiguity clarification, AST-level safety validation, and read-only execution."
    )
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # Database Configuration
    DATABASE_URL: str | None = Field(default=None, description="Direct PostgreSQL connection string (DSN)")
    DB_NAME: str = Field(default="text_to_sql_store", description="PostgreSQL database name")
    DB_USER: str = Field(default="postgres", description="PostgreSQL username")
    DB_PASSWORD: str = Field(default="postgres", description="PostgreSQL password")
    DB_HOST: str = Field(default="localhost", description="PostgreSQL host")
    DB_PORT: int = Field(default=5432, description="PostgreSQL port")

    # Connection Pool Settings
    DB_POOL_MIN_CONN: int = Field(default=2, description="Minimum pool connections")
    DB_POOL_MAX_CONN: int = Field(default=10, description="Maximum pool connections")
    DB_STATEMENT_TIMEOUT_MS: int = Field(default=5000, description="Read-only query timeout in ms")
    SCHEMA_CACHE_TTL_SECONDS: int = Field(default=300, description="Schema introspection cache TTL")

    # Query Execution Limits
    MAX_QUERY_LIMIT: int = Field(default=10, description="Default LIMIT appended to generated queries")
    MAX_ALLOWED_LIMIT: int = Field(default=100, description="Maximum rows allowed for any execution")

    # LLM Provider Configuration (Default: Groq - Free & Fast)
    LLM_PROVIDER: str = Field(default="groq", description="LLM provider name: groq, openai, ollama, etc.")
    LLM_BASE_URL: str = Field(default="https://api.groq.com/openai/v1", description="OpenAI-compatible base URL")
    LLM_API_KEY: str | None = Field(default=None, description="API Key for the LLM provider (e.g. Groq or OpenAI)")
    LLM_MODEL: str = Field(default="qwen/qwen3.8-27b", description="Model identifier (e.g. qwen/qwen3.8-27b, llama-3.3-70b-versatile)")

    # Backward compatibility aliases
    OPENAI_API_KEY: str | None = Field(default=None, description="Legacy alias for LLM_API_KEY")
    OPENAI_MODEL: str | None = Field(default=None, description="Legacy alias for LLM_MODEL")

    @property
    def active_llm_api_key(self) -> str | None:
        return self.LLM_API_KEY or self.OPENAI_API_KEY

    @property
    def active_llm_model(self) -> str:
        return self.LLM_MODEL or self.OPENAI_MODEL or "llama-3.3-70b-versatile"

    # API Security & Rate Limiting
    API_KEY_ENABLED: bool = Field(default=False, description="Enable API key authentication")
    API_KEY: str | None = Field(default=None, description="Secret API key for endpoint protection")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="Max requests allowed per minute per IP")

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
