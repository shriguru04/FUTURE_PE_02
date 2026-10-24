from urllib.parse import urlparse

from app.ai.base import LLMProvider, ProviderNotConfigured
from app.ai.mock import MockProvider
from app.ai.openai_compat import OpenAICompatProvider
from app.core.config import Settings

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "host.docker.internal", "ollama"}


def is_configured(s: Settings) -> bool:
    if s.llm_provider == "mock":
        return not s.is_production
    host = urlparse(s.llm_base_url).hostname or ""
    return bool(s.llm_api_key) or host in _LOCAL_HOSTS


def build_provider(s: Settings) -> LLMProvider:
    if s.llm_provider == "mock":
        if s.is_production:
            raise ProviderNotConfigured("The mock provider is disabled in production. Configure LLM_API_KEY.")
        return MockProvider()
    if s.llm_provider != "openai_compat":
        raise ProviderNotConfigured(f"Unknown LLM_PROVIDER '{s.llm_provider}'.")
    if not is_configured(s):
        raise ProviderNotConfigured(
            "No LLM provider is configured. Set LLM_API_KEY (and LLM_BASE_URL / LLM_MODEL) in the backend environment."
        )
    return OpenAICompatProvider(s.llm_base_url, s.llm_api_key, s.llm_model, s.llm_timeout_seconds, s.llm_json_mode)
