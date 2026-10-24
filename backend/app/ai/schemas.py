"""Pydantic models describing what the LLM must return and what each stored section looks like."""
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Scene(BaseModel):
    scene_number: int = Field(ge=1)
    duration_seconds: int = Field(ge=1, le=120)
    visual_direction: str = Field(min_length=1)
    dialogue: str = ""
    on_screen_text: str = ""
    transition: str = ""
    audio_direction: str = ""


class Script(BaseModel):
    title: str = Field(min_length=1)
    total_duration_seconds: int = Field(ge=1, le=300)
    scenes: list[Scene] = Field(min_length=1)
    voice_over: str = ""


class ClaimReviewItem(BaseModel):
    claim: str = Field(min_length=1)
    status: Literal["supported", "unsupported", "needs_verification"]
    note: str = ""


class PlatformAdaptation(BaseModel):
    hook_style: str = ""
    pacing: str = ""
    suggested_duration_seconds: int = Field(default=30, ge=1, le=300)
    visual_format: str = ""
    caption_structure: str = ""
    cta_placement: str = ""
    hashtag_strategy: str = ""


class CampaignPack(BaseModel):
    summary: str = Field(min_length=1)
    hooks: list[str] = Field(min_length=1)
    primary_script: Script
    alternative_scripts: list[Script] = []
    caption: str = Field(min_length=1)
    primary_cta: str = Field(min_length=1)
    alternative_ctas: list[str] = []
    hashtags: list[str] = []
    variations: list[str] = []
    adaptation: PlatformAdaptation
    claims_review: list[ClaimReviewItem] = []

    @field_validator("hooks")
    @classmethod
    def _hooks_not_blank(cls, v):
        v = [h.strip() for h in v if h and h.strip()]
        if not v:
            raise ValueError("hooks must contain non-empty text")
        return v


# ---- Stored per-section payloads (also used to validate manual edits) ----
class TextPayload(BaseModel):
    text: str = Field(min_length=1)


class ListPayload(BaseModel):
    items: list[str] = Field(max_length=100)


class ScriptList(BaseModel):
    items: list[Script] = Field(max_length=20)


class CtaPayload(BaseModel):
    primary: str = Field(min_length=1)
    alternatives: list[str] = []


class ClaimList(BaseModel):
    items: list[ClaimReviewItem]


SECTION_MODELS: dict[str, type[BaseModel]] = {
    "summary": TextPayload,
    "hooks": ListPayload,
    "primary_script": Script,
    "alt_scripts": ScriptList,
    "caption": TextPayload,
    "ctas": CtaPayload,
    "hashtags": ListPayload,
    "variations": ListPayload,
    "adaptation": PlatformAdaptation,
    "claims_review": ClaimList,
}


def pack_to_sections(pack: CampaignPack) -> dict[str, dict]:
    return {
        "summary": {"text": pack.summary},
        "hooks": {"items": pack.hooks},
        "primary_script": pack.primary_script.model_dump(),
        "alt_scripts": {"items": [s.model_dump() for s in pack.alternative_scripts]},
        "caption": {"text": pack.caption},
        "ctas": {"primary": pack.primary_cta, "alternatives": pack.alternative_ctas},
        "hashtags": {"items": pack.hashtags},
        "variations": {"items": pack.variations},
        "adaptation": pack.adaptation.model_dump(),
        "claims_review": {"items": [c.model_dump() for c in pack.claims_review]},
    }
