import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import PageParams, apply_update, audit, commit_or_conflict, get_current_user, paginated
from app.core.constants import PLATFORMS, STATUSES
from app.core.database import get_db
from app.core.errors import APIError
from app.models import Brand, Campaign, CampaignContent, Product, User
from app.repositories.base import OwnedRepo, like_pattern
from app.schemas.campaign import CampaignCreate, CampaignOut, CampaignUpdate
from app.schemas.common import Page
from app.services.content import save_section

router = APIRouter(prefix="/campaigns", tags=["campaigns"])
NON_NULL = {"name", "objective", "platform", "status", "notes", "settings"}


def _check_product(db: Session, user: User, brand_id: uuid.UUID, product_id: uuid.UUID | None) -> None:
    if product_id is None:
        return
    product = OwnedRepo(Product, db, user.id).get_or_404(product_id, "Product")
    if product.brand_id != brand_id:
        raise APIError(422, "product_brand_mismatch", "The product does not belong to the selected brand.")


@router.get("", response_model=Page[CampaignOut])
def list_campaigns(q: str | None = Query(None, max_length=100), status: str | None = Query(None),
                   platform: str | None = Query(None), brand_id: uuid.UUID | None = None,
                   p: PageParams = Depends(), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if status and status not in STATUSES:
        raise APIError(422, "validation_error", "Unknown status filter.")
    if platform and platform not in PLATFORMS:
        raise APIError(422, "validation_error", "Unknown platform filter.")
    filters = []
    if q:
        filters.append(Campaign.name.ilike(like_pattern(q), escape="\\"))
    if status:
        filters.append(Campaign.status == status)
    if platform:
        filters.append(Campaign.platform == platform)
    if brand_id:
        filters.append(Campaign.brand_id == brand_id)
    items, total = OwnedRepo(Campaign, db, user.id).list(
        *filters, order_by=[Campaign.updated_at.desc(), Campaign.id], page=p.page, page_size=p.page_size)
    return paginated(items, total, p)


@router.post("", response_model=CampaignOut, status_code=201)
def create_campaign(payload: CampaignCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    OwnedRepo(Brand, db, user.id).get_or_404(payload.brand_id, "Brand")
    _check_product(db, user, payload.brand_id, payload.product_id)
    campaign = Campaign(user_id=user.id, **payload.model_dump())
    db.add(campaign)
    audit(db, user.id, "campaign.create", "campaign", campaign.id)
    db.commit()
    return campaign


@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(campaign_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return OwnedRepo(Campaign, db, user.id).get_or_404(campaign_id, "Campaign")


@router.patch("/{campaign_id}", response_model=CampaignOut)
def update_campaign(campaign_id: uuid.UUID, payload: CampaignUpdate, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    campaign = OwnedRepo(Campaign, db, user.id).get_or_404(campaign_id, "Campaign")
    data = payload.model_dump(exclude_unset=True)
    if "product_id" in data:
        _check_product(db, user, campaign.brand_id, data["product_id"])
    apply_update(campaign, data, NON_NULL)
    db.commit()
    return campaign


@router.delete("/{campaign_id}", status_code=204)
def delete_campaign(campaign_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    campaign = OwnedRepo(Campaign, db, user.id).get_or_404(campaign_id, "Campaign")
    db.delete(campaign)  # contents, versions, metrics, jobs: ON DELETE CASCADE
    audit(db, user.id, "campaign.delete", "campaign", campaign_id)
    commit_or_conflict(db, "Could not delete the campaign.")
    return Response(status_code=204)


@router.post("/{campaign_id}/duplicate", response_model=CampaignOut, status_code=201)
def duplicate_campaign(campaign_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    src = OwnedRepo(Campaign, db, user.id).get_or_404(campaign_id, "Campaign")
    copy = Campaign(user_id=user.id, brand_id=src.brand_id, product_id=src.product_id, name=f"{src.name} (copy)"[:200],
                    objective=src.objective, platform=src.platform, status="draft", settings=dict(src.settings or {}),
                    notes=src.notes)
    db.add(copy)
    db.flush()
    for c in db.scalars(select(CampaignContent).where(CampaignContent.campaign_id == src.id,
                                                      CampaignContent.user_id == user.id)):
        save_section(db, user_id=user.id, campaign_id=copy.id, platform=c.platform, section=c.section,
                     payload=c.payload, source="duplicate", generation_params={"duplicated_from": str(src.id)})
    audit(db, user.id, "campaign.duplicate", "campaign", copy.id)
    db.commit()
    return copy
