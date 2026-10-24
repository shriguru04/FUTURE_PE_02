import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    JSON, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer,
    Numeric, String, Text, UniqueConstraint, Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import METRIC_SOURCES, PLATFORMS, SECTIONS, STATUSES, VERSION_SOURCES
from app.core.database import Base

JSONType = JSON().with_variant(JSONB(), "postgresql")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _in(col: str, values) -> str:
    return f"{col} IN ({', '.join(repr(v) for v in values)})"


def owner_fk():
    """Explicit ownership: every user-owned row points at users.id."""
    return mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)


class IdMixin:
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


class TimeMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class User(IdMixin, TimeMixin, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(120), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Brand(IdMixin, TimeMixin, Base):
    __tablename__ = "brands"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_brands_user_name"),)
    user_id: Mapped[uuid.UUID] = owner_fk()
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(300), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    target_audience: Mapped[str] = mapped_column(Text, default="")
    voice: Mapped[str] = mapped_column(String(300), default="")
    language: Mapped[str] = mapped_column(String(300), default="English")
    writing_style: Mapped[str] = mapped_column(String(300), default="")
    messaging_guidelines: Mapped[str] = mapped_column(Text, default="")
    avoid_terms: Mapped[list] = mapped_column(JSONType, default=list)
    website_url: Mapped[str] = mapped_column(String(500), default="")
    default_cta: Mapped[str] = mapped_column(String(300), default="")


class Product(IdMixin, TimeMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("brand_id", "name", name="uq_products_brand_name"),
        CheckConstraint("price IS NULL OR price >= 0", name="ck_products_price"),
    )
    user_id: Mapped[uuid.UUID] = owner_fk()
    brand_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("brands.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    features: Mapped[list] = mapped_column(JSONType, default=list)
    benefits: Mapped[list] = mapped_column(JSONType, default=list)
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    intended_audience: Mapped[str] = mapped_column(Text, default="")
    supported_claims: Mapped[list] = mapped_column(JSONType, default=list)
    limitations: Mapped[str] = mapped_column(Text, default="")
    offer_details: Mapped[str] = mapped_column(Text, default="")
    cta: Mapped[str] = mapped_column(String(300), default="")


class Campaign(IdMixin, TimeMixin, Base):
    __tablename__ = "campaigns"
    __table_args__ = (
        CheckConstraint(_in("platform", PLATFORMS), name="ck_campaigns_platform"),
        CheckConstraint(_in("status", STATUSES), name="ck_campaigns_status"),
        Index("ix_campaigns_user_status", "user_id", "status"),
        Index("ix_campaigns_user_platform", "user_id", "platform"),
    )
    user_id: Mapped[uuid.UUID] = owner_fk()
    brand_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("brands.id", ondelete="RESTRICT"), index=True)
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="SET NULL"), index=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String(200))
    objective: Mapped[str] = mapped_column(Text, default="")
    platform: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="draft")
    settings: Mapped[dict] = mapped_column(JSONType, default=dict)
    notes: Mapped[str] = mapped_column(Text, default="")


class CampaignContent(IdMixin, TimeMixin, Base):
    __tablename__ = "campaign_contents"
    __table_args__ = (
        UniqueConstraint("campaign_id", "platform", "section", name="uq_content_campaign_platform_section"),
        CheckConstraint(_in("platform", PLATFORMS), name="ck_content_platform"),
        CheckConstraint(_in("section", SECTIONS), name="ck_content_section"),
    )
    user_id: Mapped[uuid.UUID] = owner_fk()
    campaign_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("campaigns.id", ondelete="CASCADE"), index=True)
    platform: Mapped[str] = mapped_column(String(30))
    section: Mapped[str] = mapped_column(String(30))
    payload: Mapped[dict] = mapped_column(JSONType)
    current_version: Mapped[int] = mapped_column(Integer, default=1)


class ContentVersion(IdMixin, Base):
    __tablename__ = "content_versions"
    __table_args__ = (
        UniqueConstraint("content_id", "version_number", name="uq_versions_content_number"),
        CheckConstraint(_in("source", VERSION_SOURCES), name="ck_versions_source"),
    )
    user_id: Mapped[uuid.UUID] = owner_fk()
    campaign_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("campaigns.id", ondelete="CASCADE"), index=True)
    content_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("campaign_contents.id", ondelete="CASCADE"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSONType)
    source: Mapped[str] = mapped_column(String(30))
    generation_params: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CampaignMetric(IdMixin, TimeMixin, Base):
    __tablename__ = "campaign_metrics"
    __table_args__ = (
        UniqueConstraint("campaign_id", "metric_date", "source", name="uq_metrics_campaign_date_source"),
        CheckConstraint(_in("source", METRIC_SOURCES), name="ck_metrics_source"),
        CheckConstraint("impressions IS NULL OR impressions >= 0", name="ck_metrics_impressions"),
        CheckConstraint("reach IS NULL OR reach >= 0", name="ck_metrics_reach"),
        CheckConstraint("video_views IS NULL OR video_views >= 0", name="ck_metrics_views"),
        CheckConstraint("clicks IS NULL OR clicks >= 0", name="ck_metrics_clicks"),
        CheckConstraint("conversions IS NULL OR conversions >= 0", name="ck_metrics_conversions"),
        CheckConstraint("spend IS NULL OR spend >= 0", name="ck_metrics_spend"),
        CheckConstraint("revenue IS NULL OR revenue >= 0", name="ck_metrics_revenue"),
    )
    user_id: Mapped[uuid.UUID] = owner_fk()
    campaign_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("campaigns.id", ondelete="CASCADE"), index=True)
    metric_date: Mapped[date] = mapped_column(Date)
    impressions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reach: Mapped[int | None] = mapped_column(Integer, nullable=True)
    video_views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clicks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conversions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    spend: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    revenue: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="manual")


class GenerationJob(IdMixin, Base):
    __tablename__ = "generation_jobs"
    __table_args__ = (CheckConstraint(_in("status", ("running", "succeeded", "failed")), name="ck_jobs_status"),)
    user_id: Mapped[uuid.UUID] = owner_fk()
    campaign_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("campaigns.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20))  # full | section
    platform: Mapped[str] = mapped_column(String(30))
    section: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="running")
    provider: Mapped[str] = mapped_column(String(50), default="")
    model: Mapped[str] = mapped_column(String(100), default="")
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditEvent(IdMixin, Base):
    __tablename__ = "audit_events"
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    action: Mapped[str] = mapped_column(String(60))
    entity_type: Mapped[str] = mapped_column(String(40), default="")
    entity_id: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
