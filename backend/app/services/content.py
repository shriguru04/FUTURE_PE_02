"""Content persistence + version history. Every write creates a new ContentVersion; history is never rewritten."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CampaignContent, ContentVersion


def save_section(
    db: Session, *, user_id: uuid.UUID, campaign_id: uuid.UUID, platform: str, section: str,
    payload: dict, source: str, generation_params: dict | None = None,
) -> tuple[CampaignContent, ContentVersion]:
    content = db.scalar(
        select(CampaignContent)
        .where(CampaignContent.campaign_id == campaign_id, CampaignContent.platform == platform,
               CampaignContent.section == section)
        .with_for_update()  # serialises concurrent version-number allocation on PostgreSQL
    )
    if content is None:
        content = CampaignContent(user_id=user_id, campaign_id=campaign_id, platform=platform,
                                  section=section, payload=payload, current_version=0)
        db.add(content)
        db.flush()
    number = content.current_version + 1
    content.payload = payload
    content.current_version = number
    version = ContentVersion(
        user_id=user_id, campaign_id=campaign_id, content_id=content.id, version_number=number,
        payload=payload, source=source, generation_params=generation_params,
    )
    db.add(version)
    db.flush()
    return content, version
