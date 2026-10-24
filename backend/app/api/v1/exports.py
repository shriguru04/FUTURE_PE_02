import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import audit, get_current_user
from app.core.database import get_db
from app.core.errors import APIError
from app.exports.render import RENDERERS, slugify
from app.models import Brand, Campaign, CampaignContent, Product, User
from app.repositories.base import OwnedRepo
from app.schemas.campaign import ExportRequest
from app.services.generation import load_platforms

router = APIRouter(prefix="/campaigns", tags=["export"])


@router.post("/{campaign_id}/export")
def export_campaign(campaign_id: uuid.UUID, body: ExportRequest, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    campaign = OwnedRepo(Campaign, db, user.id).get_or_404(campaign_id, "Campaign")
    stmt = select(CampaignContent).where(CampaignContent.campaign_id == campaign.id, CampaignContent.user_id == user.id)
    if body.platforms:
        stmt = stmt.where(CampaignContent.platform.in_(body.platforms))
    platforms: dict[str, dict] = {}
    for c in db.scalars(stmt):
        platforms.setdefault(c.platform, {})[c.section] = c.payload
    if not platforms:
        raise APIError(409, "no_content", "There is no generated content to export yet.")
    brand = db.get(Brand, campaign.brand_id)
    product = db.get(Product, campaign.product_id) if campaign.product_id else None
    cfg = load_platforms()
    checklist = list(cfg["universal_checklist"])
    for pf in platforms:
        checklist += cfg["platforms"].get(pf, {}).get("checklist", [])
    now = datetime.now(timezone.utc)
    bundle = {
        "exported_at": now.isoformat(timespec="seconds"),
        "campaign": {"name": campaign.name, "status": campaign.status, "platform": campaign.platform,
                     "objective": campaign.objective, "notes": campaign.notes},
        "brand": {k: getattr(brand, k) for k in ("name", "category", "voice", "target_audience")},
        "product": None if product is None else {
            "name": product.name, "description": product.description, "offer_details": product.offer_details,
            "supported_claims": product.supported_claims, "limitations": product.limitations},
        "platforms": platforms, "checklist": checklist,
    }
    render, media_type = RENDERERS[body.format]
    data = render(bundle)
    filename = f"{slugify(campaign.name)}-{now:%Y%m%d}.{body.format}"
    audit(db, user.id, "campaign.export", "campaign", campaign.id)
    db.commit()
    return Response(content=data, media_type=media_type,
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})
