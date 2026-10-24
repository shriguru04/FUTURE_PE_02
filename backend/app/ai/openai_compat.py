"""One adapter for every OpenAI-compatible chat-completions API (OpenAI GPT, xAI Grok, Ollama, vLLM, ...)."""
import logging

import httpx

from app.ai.base import LLMResult, ProviderError

log = logging.getLogger("adcraft.llm")


class OpenAICompatProvider:
    name = "openai_compat"
    is_mock = False

    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 90, json_mode: bool = True):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.json_mode = json_mode

    def _post(self, body: dict) -> httpx.Response:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            return httpx.post(f"{self.base_url}/chat/completions", json=body, headers=headers, timeout=self.timeout)
        except httpx.TimeoutException as exc:
            raise ProviderError("provider_timeout", "The AI provider timed out.", retryable=True) from exc
        except httpx.HTTPError as exc:
            raise ProviderError("provider_unreachable", "Could not reach the AI provider.", retryable=True) from exc

    def complete(self, system: str, user: str) -> LLMResult:
        body = {
            "model": self.model,
            "temperature": 0.8,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        if self.json_mode:
            body["response_format"] = {"type": "json_object"}
        resp = self._post(body)
        if resp.status_code == 400 and self.json_mode:
            # Some servers reject response_format; retry once without it. Output is still validated.
            body.pop("response_format", None)
            resp = self._post(body)
        if resp.status_code in (401, 403):
            raise ProviderError("provider_auth", "The AI provider rejected the API key.", retryable=False)
        if resp.status_code == 429:
            raise ProviderError("provider_rate_limited", "The AI provider rate limit or quota was hit.", retryable=True)
        if resp.status_code >= 500:
            raise ProviderError("provider_unavailable", "The AI provider is temporarily unavailable.", retryable=True)
        if resp.status_code >= 400:
            log.warning("provider returned HTTP %s", resp.status_code)  # body deliberately not logged
            raise ProviderError("provider_bad_request", f"The AI provider rejected the request (HTTP {resp.status_code}).")
        try:
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderError("provider_bad_response", "The AI provider returned an unexpected response.", True) from exc
        usage = data.get("usage") or {}
        return LLMResult(
            text=text or "",
            model=data.get("model", self.model),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
        )
