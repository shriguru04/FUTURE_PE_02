"""Deterministic provider for automated tests and keyless local development.
Never available when APP_ENV=production. Output is labelled so it cannot be mistaken for real AI output."""
import json
import re

from app.ai.base import LLMResult, ProviderError

LABEL = "[MOCK PROVIDER OUTPUT] "


def _scene(n: int, product: str) -> dict:
    return {
        "scene_number": n, "duration_seconds": 5,
        "visual_direction": f"Creator holds {product} and talks to camera (scene {n}).",
        "dialogue": f"Mock dialogue for scene {n}.", "on_screen_text": f"Mock text {n}",
        "transition": "Quick cut", "audio_direction": "Upbeat low-volume track",
    }


def _script(title: str, product: str) -> dict:
    return {"title": title, "total_duration_seconds": 15,
            "scenes": [_scene(i, product) for i in (1, 2, 3)], "voice_over": "Mock voice-over."}


def build_payload(prompt: str) -> dict:
    task = (re.search(r"^TASK: (.+)$", prompt, re.M) or [None, "full_pack"])[1].strip()
    product = (re.search(r"^PRODUCT: (.+)$", prompt, re.M) or [None, "the product"])[1].strip()
    n_hooks = int((re.search(r"^NUM_HOOKS: (\d+)$", prompt, re.M) or [None, "5"])[1])
    n_var = int((re.search(r"^NUM_VARIATIONS: (\d+)$", prompt, re.M) or [None, "3"])[1])
    pack = {
        "summary": f"{LABEL}Campaign summary for {product}.",
        "hooks": [f"Mock hook {i + 1} for {product}" for i in range(n_hooks)],
        "primary_script": _script("Mock primary script", product),
        "alternative_scripts": [_script("Mock alternative script", product)],
        "caption": f"{LABEL}Mock caption for {product}.",
        "primary_cta": "Learn more", "alternative_ctas": ["Shop now", "Try it today"],
        "hashtags": ["#mock", "#adcraft", "#ugc"],
        "variations": [f"Mock test variation {i + 1}" for i in range(n_var)],
        "adaptation": {"hook_style": "mock", "pacing": "mock", "suggested_duration_seconds": 15,
                       "visual_format": "9:16", "caption_structure": "mock",
                       "cta_placement": "end", "hashtag_strategy": "mock"},
        "claims_review": [{"claim": f"{product} is a product", "status": "needs_verification", "note": "mock"}],
    }
    if task.startswith("section "):
        section = task.split(" ", 1)[1]
        return {
            "summary": {"text": pack["summary"]}, "hooks": {"items": pack["hooks"]},
            "primary_script": pack["primary_script"], "alt_scripts": {"items": pack["alternative_scripts"]},
            "caption": {"text": pack["caption"]},
            "ctas": {"primary": pack["primary_cta"], "alternatives": pack["alternative_ctas"]},
            "hashtags": {"items": pack["hashtags"]}, "variations": {"items": pack["variations"]},
            "adaptation": pack["adaptation"], "claims_review": {"items": pack["claims_review"]},
        }[section]
    return pack


class MockProvider:
    name = "mock"
    model = "mock-model"
    is_mock = True

    def __init__(self, script: list[str] | None = None):
        """script: modes consumed one per call (last repeats): ok | malformed | wrong_schema | error | fatal."""
        self.script = list(script or ["ok"])
        self.calls = 0

    def complete(self, system: str, user: str) -> LLMResult:
        mode = self.script[min(self.calls, len(self.script) - 1)]
        self.calls += 1
        if mode == "error":
            raise ProviderError("provider_unavailable", "mock transient failure", retryable=True)
        if mode == "fatal":
            raise ProviderError("provider_auth", "mock auth failure", retryable=False)
        if mode == "malformed":
            return LLMResult(text="Sure! Here is your campaign: {not valid json", model=self.model)
        if mode == "wrong_schema":
            return LLMResult(text=json.dumps({"summary": "only a summary"}), model=self.model)
        return LLMResult(text=json.dumps(build_payload(user)), model=self.model, prompt_tokens=10, completion_tokens=20)
