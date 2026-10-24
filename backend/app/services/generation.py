"""Orchestrates campaign generation: context -> prompt -> provider -> validation -> persistence."""
import json
import time
import uuid
from functools import lru_cache
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import prompts
from app.ai.base import LLMProvider
from app.ai.generator import GenerationError, run_structured
from app.ai.jsonutil import normalize_hashtags
from app.ai.review import review_claims
from app.ai.schemas import SECTION_MODELS, CampaignPack, pack_to_sections
from app.core.config import get_settings
from app.core.errors import APIError
from app.models import Brand, Campaign, CampaignContent, GenerationJob, Product
from app.services.content import save_section

PLATFORMS_FILE = Path(__file__).resolve().parent.parent / "config" / "platforms.json"


@lru_cache
def load_platforms() -> dict:
    return json.loads(PLATFORMS_FILE.read_text(encoding="utf-8"))


def _brand_dict(b: Brand) -> dict:
    return {k: getattr(b, k) for k in ("name", "category", "description", "target_audience", "voice", "language",
                                       "writing_style", "messaging_guidelines", "avoid_terms", "default_cta")}


def _product_dict(p: Product | None) -> dict | None:
    if p is None:
        return None
    d = {k: getattr(p, k) for k in ("name", "description", "features", "benefits", "intended_audience",
                                    "supported_claims", "limitations", "offer_details", "cta")}
    d["price"] = None if p.price is None else float(p.price)
    return d


def build_context(db: Session, campaign: Campaign, platform: str, req: dict) -> dict:
    brand = db.get(Brand, campaign.brand_id)
    product = db.get(Product, campaign.product_id) if campaign.product_id else None
    req = dict(req)
    req["language"] = req.get("language") or brand.language or "English"
    return {
        "brand": _brand_dict(brand), "product": _product_dict(product), "platform": platform,
        "campaign": {"name": campaign.name, "objective": campaign.objective},
        "guidelines": load_platforms()["platforms"].get(platform, {}), "req": req,
    }


def _run(provider: LLMProvider, system: str, user: str, model_cls, post_validate=None):
    s = get_settings()
    return run_structured(provider, system, user, model_cls, max_retries=s.llm_max_retries,
                          backoff=s.llm_retry_backoff_seconds, post_validate=post_validate)


def _job(db: Session, user_id, campaign_id, kind: str, platform: str, section, provider: LLMProvider) -> GenerationJob:
    job = GenerationJob(user_id=user_id, campaign_id=campaign_id, kind=kind, platform=platform, section=section,
                        status="running", provider=provider.name, model=provider.model)
    db.add(job)
    db.commit()  # persisted before the (slow) provider call so failures are recorded
    return job


def _finish(db: Session, job: GenerationJob, started: float, usage=None, error: str | None = None) -> None:
    job.status = "failed" if error else "succeeded"
    job.error_code = error
    job.duration_ms = int((time.monotonic() - started) * 1000)
    if usage:
        job.model = usage.model or job.model
        job.prompt_tokens, job.completion_tokens = usage.prompt_tokens, usage.completion_tokens


def generate_platform(db: Session, provider: LLMProvider, campaign: Campaign, platform: str, req: dict) -> None:
    ctx = build_context(db, campaign, platform, req)
    job = _job(db, campaign.user_id, campaign.id, "full", platform, None, provider)
    started = time.monotonic()
    want = req["num_hooks"]

    def check(pack: CampaignPack) -> None:
        distinct = {h.strip().lower() for h in pack.hooks}
        if len(distinct) < want:
            raise ValueError(f"Expected {want} distinct hooks but got {len(distinct)}.")

    try:
        user_prompt = prompts.full_pack_prompt(ctx, CampaignPack.model_json_schema())
        pack, usage = _run(provider, prompts.system_prompt(ctx["req"]["language"]), user_prompt, CampaignPack, check)
    except GenerationError as exc:
        _finish(db, job, started, error=exc.code)
        db.commit()
        raise
    sections = pack_to_sections(pack)
    sections["hooks"]["items"] = list(dict.fromkeys(h.strip() for h in sections["hooks"]["items"]))
    sections["hashtags"]["items"] = normalize_hashtags(sections["hashtags"]["items"])
    product = ctx["product"] or {}
    sections["claims_review"]["items"] = review_claims(
        sections["claims_review"]["items"], product.get("supported_claims", []), ctx["brand"]["avoid_terms"], sections
    )
    params = {"request": req, "platform": platform, "provider": provider.name, "model": usage.model or provider.model,
              "is_mock": provider.is_mock, "attempts": usage.attempts,
              "context_snapshot": {"brand": ctx["brand"]["name"], "product": product.get("name")}}
    for section, payload in sections.items():
        save_section(db, user_id=campaign.user_id, campaign_id=campaign.id, platform=platform, section=section,
                     payload=payload, source="generation", generation_params=params)
    if campaign.status == "draft":
        campaign.status = "in_progress"
    campaign.settings = {**(campaign.settings or {}), "last_generation": req}
    _finish(db, job, started, usage)
    db.commit()


def regenerate_section(db: Session, provider: LLMProvider, campaign: Campaign, platform: str, section: str,
                       instruction: str) -> None:
    settings_req = (campaign.settings or {}).get("last_generation") or {}
    req = {"content_format": "problem_solution", "duration_seconds": 30, "num_hooks": 5, "num_variations": 3,
           **settings_req}
    ctx = build_context(db, campaign, platform, req)
    current = db.scalar(select(CampaignContent).where(
        CampaignContent.campaign_id == campaign.id, CampaignContent.platform == platform,
        CampaignContent.section == section))
    model_cls = SECTION_MODELS[section]
    job = _job(db, campaign.user_id, campaign.id, "section", platform, section, provider)
    started = time.monotonic()
    try:
        user_prompt = prompts.section_prompt(ctx, section, model_cls.model_json_schema(),
                                             current.payload if current else None, instruction)
        obj, usage = _run(provider, prompts.system_prompt(ctx["req"]["language"]), user_prompt, model_cls)
    except GenerationError as exc:
        _finish(db, job, started, error=exc.code)
        db.commit()
        raise
    payload = obj.model_dump()
    if section == "hashtags":
        payload["items"] = normalize_hashtags(payload["items"])
    params = {"platform": platform, "section": section, "instruction": instruction, "provider": provider.name,
              "model": usage.model or provider.model, "is_mock": provider.is_mock, "attempts": usage.attempts}
    save_section(db, user_id=campaign.user_id, campaign_id=campaign.id, platform=platform, section=section,
                 payload=payload, source="section_regeneration", generation_params=params)
    _finish(db, job, started, usage)
    db.commit()


def to_api_error(exc: GenerationError) -> APIError:
    return APIError(exc.status, exc.code, exc.message)
