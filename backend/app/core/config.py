from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_DEFAULT_KEY = "change-me-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "sqlite:///./adcraft.db"
    secret_key: str = INSECURE_DEFAULT_KEY
    access_token_minutes: int = 60
    cookie_name: str = "adcraft_token"
    cookie_secure: bool = False
    allowed_origins: str = "http://localhost:5173,http://localhost:8080"

    rate_limit_enabled: bool = True
    rate_limit_auth: str = "10/minute"
    rate_limit_generate: str = "10/minute"

    # LLM: any OpenAI-compatible endpoint (OpenAI GPT, xAI Grok, Ollama, vLLM...).
    llm_provider: str = "openai_compat"  # openai_compat | mock (mock refused in production)
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_json_mode: bool = True
    llm_timeout_seconds: int = 90
    llm_max_retries: int = 2
    llm_retry_backoff_seconds: float = 1.0

    log_level: str = "INFO"

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.is_production:
        if s.secret_key == INSECURE_DEFAULT_KEY or len(s.secret_key) < 32:
            raise RuntimeError("SECRET_KEY must be a random value of at least 32 characters in production.")
        if not s.cookie_secure:
            raise RuntimeError("COOKIE_SECURE must be true in production (serve over HTTPS).")
    return s
