from dataclasses import dataclass
from typing import Protocol


@dataclass
class LLMResult:
    text: str
    model: str = ""
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class ProviderError(Exception):
    def __init__(self, code: str, message: str, retryable: bool = False):
        super().__init__(message)
        self.code, self.message, self.retryable = code, message, retryable


class ProviderNotConfigured(ProviderError):
    def __init__(self, message: str):
        super().__init__("provider_not_configured", message, retryable=False)


class LLMProvider(Protocol):
    name: str
    model: str
    is_mock: bool

    def complete(self, system: str, user: str) -> LLMResult: ...
