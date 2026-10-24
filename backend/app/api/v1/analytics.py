import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import audit, commit_or_conflict, get_current_user
from app.core.database import get_db
from app.core.errors import APIError
from app.models import Campaign, CampaignMetric, GenerationJob, User
from app.repositories.base import OwnedRepo
from app.schemas.campaign import CampaignOut, MetricCreate, MetricOut
from app.services.analytics import FIELDS, compute_rates, summarize

router = APIRouter(tags=["analytics"])
DATA_SOURCE = "manual_entry"
DISCLAIMER = ("These figures were typed in by you. AdCraft AI is not connected to Instagram, Facebook, YouTube "
              "or any ad platform and does not pull live analytics.")


def _f(v):
    return None if v is None else float(v)


def metric_dict(m: CampaignMetric) -> dict:
    raw = {f: _f(getattr(m, f)) if f in ("spend", "revenue") else getattr(m, f) for f in FIELDS}
    return {"id": m.id, "metric_date": m.metric_date, "source": m.source, **raw, **compute_rates(raw)}


@router.post("/campaigns/{campaign_id}/metrics", response_model=MetricOut, status_code=201)
def add_metric(campaign_id: uuid.UUID, body: MetricCreate, user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    campaign = OwnedRepo(Campaign, db, user.id).get_or_404(campaign_id, "Campaign")
    if db.scalar(select(CampaignMetric.id).where(CampaignMetric.campaign_id == campaign.id,
                                                 CampaignMetric.metric_date == body.metric_date,
                                                 CampaignMetric.source == "manual")):
        raise APIError(409, "metric_exists", "Metrics for this date already exist. Delete the row to re-enter it.")
    m = CampaignMetric(user_id=user.id, campaign_id=campaign.id, source="manual", **body.model_dump())
    db.add(m)
    commit_or_conflict(db, "Metrics for this date already exist.")
    return metric_dict(m)


@router.delete("/campaigns/{campaign_id}/metrics/{metric_id}", status_code=204)
def delete_metric(campaign_id: uuid.UUID, metric_id: uuid.UUID, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    campaign = OwnedRepo(Campaign, db, user.id).get_or_404(campaign_id, "Campaign")
    m = OwnedRepo(CampaignMetric, db, user.id).first(CampaignMetric.id == metric_id,
                                                      CampaignMetric.campaign_id == campaign.id)
    if m is None:
        raise APIError(404, "not_found", "Metric row not found.")
    db.delete(m)
    db.commit()
    return Response(status_code=204)


@router.get("/campaigns/{campaign_id}/analytics")
def campaign_analytics(campaign_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    campaign = OwnedRepo(Campaign, db, user.id).get_or_404(campaign_id, "Campaign")
    rows = db.scalars(select(CampaignMetric).where(CampaignMetric.campaign_id == campaign.id,
                                                   CampaignMetric.user_id == user.id)
                      .order_by(CampaignMetric.metric_date)).all()
    dicts = [metric_dict(r) for r in rows]
    return {"campaign_id": campaign.id, "data_source": DATA_SOURCE, "disclaimer": DISCLAIMER,
            "has_data": bool(dicts), "rows": dicts, **summarize(dicts)}


@router.get("/analytics/overview")
def overview(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    camp = OwnedRepo(Campaign, db, user.id)
    by_status = dict(db.execute(select(Campaign.status, func.count()).where(Campaign.user_id == user.id)
                                .group_by(Campaign.status)).all())
    by_platform = dict(db.execute(select(Campaign.platform, func.count()).where(Campaign.user_id == user.id)
                                  .group_by(Campaign.platform)).all())
    recent, _ = camp.list(order_by=[Campaign.updated_at.desc()], page=1, page_size=5)
    drafts, _ = camp.list(Campaign.status == "draft", order_by=[Campaign.updated_at.desc()], page=1, page_size=5)
    jobs = db.execute(
        select(GenerationJob, Campaign.name).join(Campaign, Campaign.id == GenerationJob.campaign_id)
        .where(GenerationJob.user_id == user.id, GenerationJob.status == "succeeded")
        .order_by(GenerationJob.created_at.desc()).limit(5)).all()

    sums = [func.sum(getattr(CampaignMetric, f)).label(f) for f in FIELDS]
    per_campaign_rows = db.execute(
        select(CampaignMetric.campaign_id, Campaign.name, *sums)
        .join(Campaign, Campaign.id == CampaignMetric.campaign_id)
        .where(CampaignMetric.user_id == user.id).group_by(CampaignMetric.campaign_id, Campaign.name)).all()
    per_campaign, all_totals = [], []
    for r in per_campaign_rows:
        totals = {f: _f(getattr(r, f)) for f in FIELDS}
        all_totals.append(totals)
        per_campaign.append({"campaign_id": r.campaign_id, "name": r.name, "totals": totals,
                             "rates": compute_rates(totals)})
    trend_rows = db.execute(
        select(CampaignMetric.metric_date, *sums).where(CampaignMetric.user_id == user.id)
        .group_by(CampaignMetric.metric_date).order_by(CampaignMetric.metric_date.desc()).limit(90)).all()
    trend = []
    for r in reversed(trend_rows):
        t = {f: _f(getattr(r, f)) for f in FIELDS}
        trend.append({"date": r.metric_date, **t, **compute_rates(t)})
    overall = summarize(all_totals) if all_totals else summarize([])
    return {
        "data_source": DATA_SOURCE, "disclaimer": DISCLAIMER,
        "campaign_counts": {"total": sum(by_status.values()), "by_status": by_status},
        "platform_distribution": by_platform,
        "recent_campaigns": [CampaignOut.model_validate(c).model_dump(mode="json") for c in recent],
        "draft_campaigns": [CampaignOut.model_validate(c).model_dump(mode="json") for c in drafts],
        "recent_generations": [{"campaign_id": j.campaign_id, "campaign_name": n, "platform": j.platform, "kind": j.kind,
                                "section": j.section, "provider": j.provider, "created_at": j.created_at}
                               for j, n in jobs],
        "metrics": {"has_data": bool(all_totals), "totals": overall["totals"], "rates": overall["rates"],
                    "per_campaign": per_campaign, "trend": trend},
    }
