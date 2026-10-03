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
    DB_STATEMENT_TIMEOUT_MS: int = Field(default=20000, description="Read-only query timeout in ms")
    SCHEMA_CACHE_TTL_SECONDS: int = Field(default=300, description="Schema introspection cache TTL")

    # Query Execution Limits
    MAX_QUERY_LIMIT: int = Field(default=10, description="Default LIMIT appended to generated queries")
    MAX_ALLOWED_LIMIT: int = Field(default=100, description="Maximum rows allowed for any execution")

    # LLM Provider Configuration (Default: Gemini - Google AI Studio)
    LLM_PROVIDER: str = Field(default="gemini", description="LLM provider name: gemini, groq, openai, ollama, etc.")
    LLM_BASE_URL: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta/openai/",
        description="OpenAI-compatible base URL for Gemini / OpenAI / Groq",
    )
    LLM_API_KEY: str | None = Field(default=None, description="API Key for the LLM provider (e.g. Gemini, Groq, or OpenAI)")
    LLM_MODEL: str = Field(
        default="gemini-2.5-flash",
        description="Model identifier (e.g. gemini-2.5-flash, gemini-2.0-flash, gemini-1.5-flash)",
    )

    # Provider specific aliases
    GEMINI_API_KEY: str | None = Field(default=None, description="Google Gemini API Key from Google AI Studio")
    GOOGLE_API_KEY: str | None = Field(default=None, description="Google API Key alias")
    GROQ_API_KEY: str | None = Field(default=None, description="Groq API Key alias")
    OPENAI_API_KEY: str | None = Field(default=None, description="Legacy alias for LLM_API_KEY")
    OPENAI_MODEL: str | None = Field(default=None, description="Legacy alias for LLM_MODEL")

    @property
    def active_llm_api_key(self) -> str | None:
        return (
            self.GEMINI_API_KEY
            or self.GOOGLE_API_KEY
            or self.LLM_API_KEY
            or self.OPENAI_API_KEY
            or self.GROQ_API_KEY
        )

    @property
    def active_llm_base_url(self) -> str:
        if self.LLM_PROVIDER.lower() == "gemini":
            if not self.LLM_BASE_URL or "groq.com" in self.LLM_BASE_URL:
                return "https://generativelanguage.googleapis.com/v1beta/openai/"
        elif self.LLM_PROVIDER.lower() == "groq":
            if not self.LLM_BASE_URL or "googleapis.com" in self.LLM_BASE_URL:
                return "https://api.groq.com/openai/v1"
        return self.LLM_BASE_URL or "https://generativelanguage.googleapis.com/v1beta/openai/"

    @property
    def active_llm_model(self) -> str:
        if self.LLM_MODEL:
            if self.LLM_PROVIDER.lower() == "gemini" and any(m in self.LLM_MODEL.lower() for m in ["llama", "qwen", "mistral"]):
                return "gemini-2.5-flash"
            return self.LLM_MODEL
        if self.OPENAI_MODEL:
            return self.OPENAI_MODEL
        return "gemini-2.5-flash" if self.LLM_PROVIDER.lower() == "gemini" else "llama-3.3-70b-versatile"

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
