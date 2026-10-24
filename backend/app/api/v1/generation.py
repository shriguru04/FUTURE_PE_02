import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.ai.base import LLMProvider
from app.ai.generator import GenerationError
from app.api.deps import audit, get_current_user, get_provider
from app.core.database import get_db
from app.core.errors import APIError
from app.core.ratelimit import generate_limit, limiter
from app.models import Campaign, User
from app.repositories.base import OwnedRepo
from app.schemas.campaign import GenerateRequest, GenerateResponse, GenerationItem, RegenerateRequest
from app.services import generation as svc

router = APIRouter(prefix="/campaigns", tags=["generation"])


@router.post("/{campaign_id}/generate", response_model=GenerateResponse)
@limiter.limit(generate_limit)
def generate(request: Request, campaign_id: uuid.UUID, payload: GenerateRequest,
             user: User = Depends(get_current_user), db: Session = Depends(get_db),
             provider: LLMProvider = Depends(get_provider)):
    campaign = OwnedRepo(Campaign, db, user.id).get_or_404(campaign_id, "Campaign")
    platforms = list(dict.fromkeys(payload.platforms or [campaign.platform]))
    req = payload.model_dump(exclude={"platforms"})
    results, first_error = [], None
    for platform in platforms:
        try:
            svc.generate_platform(db, provider, campaign, platform, req)
            results.append(GenerationItem(platform=platform, status="succeeded"))
        except GenerationError as exc:
            db.rollback()
            first_error = first_error or exc
            results.append(GenerationItem(platform=platform, status="failed", error_code=exc.code,
                                          error_message=exc.message))
    if all(r.status == "failed" for r in results):
        raise svc.to_api_error(first_error)  # never fabricate content to hide a provider failure
    audit(db, user.id, "campaign.generate", "campaign", campaign_id)
    db.commit()
    return GenerateResponse(provider=provider.name, model=provider.model, is_mock=provider.is_mock, results=results)


@router.post("/{campaign_id}/regenerate-section", response_model=GenerateResponse)
@limiter.limit(generate_limit)
def regenerate_section(request: Request, campaign_id: uuid.UUID, payload: RegenerateRequest,
                       user: User = Depends(get_current_user), db: Session = Depends(get_db),
                       provider: LLMProvider = Depends(get_provider)):
    campaign = OwnedRepo(Campaign, db, user.id).get_or_404(campaign_id, "Campaign")
    try:
        svc.regenerate_section(db, provider, campaign, payload.platform, payload.section, payload.instruction)
    except GenerationError as exc:
        db.rollback()
        raise svc.to_api_error(exc) from exc
    return GenerateResponse(provider=provider.name, model=provider.model, is_mock=provider.is_mock,
                            results=[GenerationItem(platform=payload.platform, status="succeeded")])
