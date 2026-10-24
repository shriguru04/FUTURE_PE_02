import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.jsonutil import normalize_hashtags
from app.ai.schemas import SECTION_MODELS
from app.api.deps import PageParams, audit, get_current_user, paginated
from app.core.database import get_db
from app.core.errors import APIError
from app.models import Campaign, CampaignContent, ContentVersion, User
from app.repositories.base import OwnedRepo
from app.schemas.campaign import ContentOut, ContentPatch, VersionOut
from app.schemas.common import Page
from app.services.content import save_section

router = APIRouter(prefix="/campaigns", tags=["content"])


def _campaign(db: Session, user: User, campaign_id: uuid.UUID) -> Campaign:
    return OwnedRepo(Campaign, db, user.id).get_or_404(campaign_id, "Campaign")


@router.get("/{campaign_id}/content", response_model=list[ContentOut])
def get_content(campaign_id: uuid.UUID, platform: str | None = Query(None), user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    campaign = _campaign(db, user, campaign_id)
    stmt = select(CampaignContent).where(CampaignContent.campaign_id == campaign.id, CampaignContent.user_id == user.id)
    if platform:
        stmt = stmt.where(CampaignContent.platform == platform)
    return db.scalars(stmt.order_by(CampaignContent.platform, CampaignContent.section)).all()


@router.patch("/{campaign_id}/content", response_model=ContentOut)
def patch_content(campaign_id: uuid.UUID, body: ContentPatch, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    campaign = _campaign(db, user, campaign_id)
    try:
        payload = SECTION_MODELS[body.section].model_validate(body.payload).model_dump()
    except ValidationError as exc:
        details = [{"loc": [str(x) for x in e["loc"]], "msg": e["msg"]} for e in exc.errors()]
        raise APIError(422, "invalid_section_payload", f"Invalid content for '{body.section}'.", details) from exc
    if body.section == "hashtags":
        payload["items"] = normalize_hashtags(payload["items"])
    existing = db.scalar(select(CampaignContent).where(
        CampaignContent.campaign_id == campaign.id, CampaignContent.platform == body.platform,
        CampaignContent.section == body.section))
    if existing and existing.payload == payload:
        return existing  # nothing changed: do not create a noise version
    content, _ = save_section(db, user_id=user.id, campaign_id=campaign.id, platform=body.platform,
                              section=body.section, payload=payload, source="manual_edit")
    audit(db, user.id, "content.edit", "campaign", campaign.id)
    db.commit()
    return content


@router.get("/{campaign_id}/versions", response_model=Page[VersionOut])
def list_versions(campaign_id: uuid.UUID, platform: str | None = None, section: str | None = None,
                  p: PageParams = Depends(), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    campaign = _campaign(db, user, campaign_id)
    base = (select(ContentVersion, CampaignContent.platform, CampaignContent.section)
            .join(CampaignContent, CampaignContent.id == ContentVersion.content_id)
            .where(ContentVersion.campaign_id == campaign.id, ContentVersion.user_id == user.id))
    if platform:
        base = base.where(CampaignContent.platform == platform)
    if section:
        base = base.where(CampaignContent.section == section)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.execute(base.order_by(ContentVersion.created_at.desc(), ContentVersion.version_number.desc())
                      .offset((p.page - 1) * p.page_size).limit(p.page_size)).all()
    items = [{"id": v.id, "content_id": v.content_id, "platform": pf, "section": sec, "version_number": v.version_number,
              "payload": v.payload, "source": v.source, "generation_params": v.generation_params,
              "created_at": v.created_at} for v, pf, sec in rows]
    return paginated(items, total, p)


@router.post("/{campaign_id}/versions/{version_id}/restore", response_model=ContentOut)
def restore_version(campaign_id: uuid.UUID, version_id: uuid.UUID, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    campaign = _campaign(db, user, campaign_id)
    version = db.scalar(select(ContentVersion).where(
        ContentVersion.id == version_id, ContentVersion.campaign_id == campaign.id, ContentVersion.user_id == user.id))
    if version is None:
        raise APIError(404, "not_found", "Version not found.")
    content = db.get(CampaignContent, version.content_id)
    # Restoring appends a NEW version; the history is never rewritten or deleted.
    content, _ = save_section(db, user_id=user.id, campaign_id=campaign.id, platform=content.platform,
                              section=content.section, payload=version.payload, source="restore",
                              generation_params={"restored_from_version": version.version_number})
    audit(db, user.id, "content.restore", "campaign", campaign.id)
    db.commit()
    return content
