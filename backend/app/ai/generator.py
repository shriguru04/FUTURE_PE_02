"""Calls a provider, validates output with Pydantic, and retries within strict bounds."""
import logging
import time
from dataclasses import dataclass
from typing import Callable

from pydantic import BaseModel, ValidationError

from app.ai.base import LLMProvider, ProviderError
from app.ai.jsonutil import extract_json

log = logging.getLogger("adcraft.generator")


class GenerationError(Exception):
    def __init__(self, code: str, message: str, status: int = 502):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


@dataclass
class Usage:
    model: str = ""
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    attempts: int = 0

    def add(self, result) -> None:
        self.model = result.model or self.model
        for f in ("prompt_tokens", "completion_tokens"):
            v = getattr(result, f)
            if v is not None:
                setattr(self, f, (getattr(self, f) or 0) + v)


def run_structured(
    provider: LLMProvider,
    system: str,
    user: str,
    model_cls: type[BaseModel],
    *,
    max_retries: int,
    backoff: float,
    post_validate: Callable[[BaseModel], None] | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[BaseModel, Usage]:
    usage = Usage()
    provider_failures = output_failures = 0
    prompt = user
    while True:
        usage.attempts += 1
        try:
            result = provider.complete(system, prompt)
        except ProviderError as exc:
            if exc.retryable and provider_failures < max_retries:
                provider_failures += 1
                sleep(backoff * (2 ** (provider_failures - 1)))
                continue
            raise GenerationError(exc.code, exc.message) from exc
        usage.add(result)
        try:
            obj = model_cls.model_validate(extract_json(result.text))
            if post_validate:
                post_validate(obj)
            return obj, usage
        except (ValueError, ValidationError) as exc:  # includes JSON errors and schema errors
            output_failures += 1
            log.warning("LLM output rejected (attempt %s): %s", usage.attempts, type(exc).__name__)
            if output_failures > max_retries:
                raise GenerationError(
                    "invalid_output",
                    f"The AI returned output that failed validation after {usage.attempts} attempts. Try again.",
                ) from exc
            prompt = (
                f"{user}\n\n## Your previous reply was rejected\n{str(exc)[:600]}\n"
                "Return ONLY corrected JSON that satisfies the schema."
            )
