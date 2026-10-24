"""initial schema

Revision ID: 0001
Revises:
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

JSONT = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")
PLATFORMS = ("instagram_reels", "facebook_video", "youtube_shorts", "tiktok", "website_video")
STATUSES = ("draft", "in_progress", "ready_for_review", "approved", "archived")
SECTIONS = ("summary", "hooks", "primary_script", "alt_scripts", "caption",
            "ctas", "hashtags", "variations", "adaptation", "claims_review")
SOURCES = ("generation", "section_regeneration", "manual_edit", "restore", "duplicate")


def _in(col, values):
    return f"{col} IN ({', '.join(repr(v) for v in values)})"


def _id():
    return sa.Column("id", sa.Uuid(), primary_key=True)


def _times():
    return [sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False)]


def _owner():
    return sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


def _fk(name, target, ondelete, nullable=False):
    return sa.Column(name, sa.Uuid(), sa.ForeignKey(target, ondelete=ondelete), nullable=nullable)


def upgrade() -> None:
    op.create_table("users", _id(),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False), *_times())
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table("brands", _id(), _owner(),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("target_audience", sa.Text(), nullable=False),
        sa.Column("voice", sa.String(300), nullable=False),
        sa.Column("language", sa.String(300), nullable=False),
        sa.Column("writing_style", sa.String(300), nullable=False),
        sa.Column("messaging_guidelines", sa.Text(), nullable=False),
        sa.Column("avoid_terms", JSONT, nullable=False),
        sa.Column("website_url", sa.String(500), nullable=False),
        sa.Column("default_cta", sa.String(300), nullable=False), *_times(),
        sa.UniqueConstraint("user_id", "name", name="uq_brands_user_name"))
    op.create_index("ix_brands_user_id", "brands", ["user_id"])

    op.create_table("products", _id(), _owner(), _fk("brand_id", "brands.id", "CASCADE"),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("features", JSONT, nullable=False),
        sa.Column("benefits", JSONT, nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=True),
        sa.Column("intended_audience", sa.Text(), nullable=False),
        sa.Column("supported_claims", JSONT, nullable=False),
        sa.Column("limitations", sa.Text(), nullable=False),
        sa.Column("offer_details", sa.Text(), nullable=False),
        sa.Column("cta", sa.String(300), nullable=False), *_times(),
        sa.UniqueConstraint("brand_id", "name", name="uq_products_brand_name"),
        sa.CheckConstraint("price IS NULL OR price >= 0", name="ck_products_price"))
    op.create_index("ix_products_user_id", "products", ["user_id"])
    op.create_index("ix_products_brand_id", "products", ["brand_id"])

    op.create_table("campaigns", _id(), _owner(), _fk("brand_id", "brands.id", "RESTRICT"),
        _fk("product_id", "products.id", "SET NULL", nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("platform", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("settings", JSONT, nullable=False),
        sa.Column("notes", sa.Text(), nullable=False), *_times(),
        sa.CheckConstraint(_in("platform", PLATFORMS), name="ck_campaigns_platform"),
        sa.CheckConstraint(_in("status", STATUSES), name="ck_campaigns_status"))
    op.create_index("ix_campaigns_user_id", "campaigns", ["user_id"])
    op.create_index("ix_campaigns_brand_id", "campaigns", ["brand_id"])
    op.create_index("ix_campaigns_product_id", "campaigns", ["product_id"])
    op.create_index("ix_campaigns_user_status", "campaigns", ["user_id", "status"])
    op.create_index("ix_campaigns_user_platform", "campaigns", ["user_id", "platform"])

    op.create_table("campaign_contents", _id(), _owner(), _fk("campaign_id", "campaigns.id", "CASCADE"),
        sa.Column("platform", sa.String(30), nullable=False),
        sa.Column("section", sa.String(30), nullable=False),
        sa.Column("payload", JSONT, nullable=False),
        sa.Column("current_version", sa.Integer(), nullable=False), *_times(),
        sa.UniqueConstraint("campaign_id", "platform", "section", name="uq_content_campaign_platform_section"),
        sa.CheckConstraint(_in("platform", PLATFORMS), name="ck_content_platform"),
        sa.CheckConstraint(_in("section", SECTIONS), name="ck_content_section"))
    op.create_index("ix_campaign_contents_user_id", "campaign_contents", ["user_id"])
    op.create_index("ix_campaign_contents_campaign_id", "campaign_contents", ["campaign_id"])

    op.create_table("content_versions", _id(), _owner(), _fk("campaign_id", "campaigns.id", "CASCADE"),
        _fk("content_id", "campaign_contents.id", "CASCADE"),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("payload", JSONT, nullable=False),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("generation_params", JSONT, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("content_id", "version_number", name="uq_versions_content_number"),
        sa.CheckConstraint(_in("source", SOURCES), name="ck_versions_source"))
    op.create_index("ix_content_versions_user_id", "content_versions", ["user_id"])
    op.create_index("ix_content_versions_campaign_id", "content_versions", ["campaign_id"])
    op.create_index("ix_content_versions_content_id", "content_versions", ["content_id"])

    nn = lambda c: f"{c} IS NULL OR {c} >= 0"  # noqa: E731
    op.create_table("campaign_metrics", _id(), _owner(), _fk("campaign_id", "campaigns.id", "CASCADE"),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=True),
        sa.Column("reach", sa.Integer(), nullable=True),
        sa.Column("video_views", sa.Integer(), nullable=True),
        sa.Column("clicks", sa.Integer(), nullable=True),
        sa.Column("conversions", sa.Integer(), nullable=True),
        sa.Column("spend", sa.Numeric(14, 2), nullable=True),
        sa.Column("revenue", sa.Numeric(14, 2), nullable=True),
        sa.Column("source", sa.String(20), nullable=False), *_times(),
        sa.UniqueConstraint("campaign_id", "metric_date", "source", name="uq_metrics_campaign_date_source"),
        sa.CheckConstraint(_in("source", ("manual", "csv_import")), name="ck_metrics_source"),
        sa.CheckConstraint(nn("impressions"), name="ck_metrics_impressions"),
        sa.CheckConstraint(nn("reach"), name="ck_metrics_reach"),
        sa.CheckConstraint(nn("video_views"), name="ck_metrics_views"),
        sa.CheckConstraint(nn("clicks"), name="ck_metrics_clicks"),
        sa.CheckConstraint(nn("conversions"), name="ck_metrics_conversions"),
        sa.CheckConstraint(nn("spend"), name="ck_metrics_spend"),
        sa.CheckConstraint(nn("revenue"), name="ck_metrics_revenue"))
    op.create_index("ix_campaign_metrics_user_id", "campaign_metrics", ["user_id"])
    op.create_index("ix_campaign_metrics_campaign_id", "campaign_metrics", ["campaign_id"])

    op.create_table("generation_jobs", _id(), _owner(), _fk("campaign_id", "campaigns.id", "CASCADE"),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("platform", sa.String(30), nullable=False),
        sa.Column("section", sa.String(30), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(50), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(_in("status", ("running", "succeeded", "failed")), name="ck_jobs_status"))
    op.create_index("ix_generation_jobs_user_id", "generation_jobs", ["user_id"])
    op.create_index("ix_generation_jobs_campaign_id", "generation_jobs", ["campaign_id"])

    op.create_table("audit_events", _id(),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(60), nullable=False),
        sa.Column("entity_type", sa.String(40), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_audit_events_user_id", "audit_events", ["user_id"])


def downgrade() -> None:
    for t in ("audit_events", "generation_jobs", "campaign_metrics", "content_versions",
              "campaign_contents", "campaigns", "products", "brands", "users"):
        op.drop_table(t)
