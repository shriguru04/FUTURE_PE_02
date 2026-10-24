import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.core.constants import CONTENT_FORMATS, EXPORT_FORMATS, PLATFORMS, SECTIONS, STATUSES
from app.schemas.common import Long, Name, ORM, Short, Timestamps

Platform = Literal[PLATFORMS]  # type: ignore[valid-type]
Status = Literal[STATUSES]  # type: ignore[valid-type]
Section = Literal[SECTIONS]  # type: ignore[valid-type]
ContentFormat = Literal[CONTENT_FORMATS]  # type: ignore[valid-type]
ExportFormat = Literal[EXPORT_FORMATS]  # type: ignore[valid-type]


class CampaignCreate(BaseModel):
    name: Name
    brand_id: uuid.UUID
    product_id: uuid.UUID | None = None
    objective: Long = ""
    platform: Platform
    notes: Long = ""
    settings: dict[str, Any] = {}


class CampaignUpdate(BaseModel):
    name: Name | None = None
    product_id: uuid.UUID | None = None
    objective: Long | None = None
    platform: Platform | None = None
    status: Status | None = None
    notes: Long | None = None
    settings: dict[str, Any] | None = None


class CampaignOut(Timestamps):
    name: str
    brand_id: uuid.UUID
    product_id: uuid.UUID | None
    objective: str
    platform: str
    status: str
    notes: str
    settings: dict[str, Any]


class GenerateRequest(BaseModel):
    platforms: list[Platform] | None = Field(default=None, min_length=1, max_length=5)
    content_format: ContentFormat = "problem_solution"
    duration_seconds: int = Field(default=30, ge=5, le=180)
    tone: Short = ""
    target_audience: Long = ""
    offer: Long = ""
    main_problem: Long = ""
    desired_cta: Short = ""
    num_hooks: int = Field(default=5, ge=1, le=10)
    num_variations: int = Field(default=3, ge=1, le=5)
    reference_content: str = Field(default="", max_length=5000)
    language: Short = ""


class RegenerateRequest(BaseModel):
    platform: Platform
    section: Section
    instruction: str = Field(default="", max_length=500)


class GenerationItem(BaseModel):
    platform: str
    status: Literal["succeeded", "failed"]
    error_code: str | None = None
    error_message: str | None = None


class GenerateResponse(BaseModel):
    provider: str
    model: str
    is_mock: bool
    results: list[GenerationItem]


class ContentOut(ORM):
    id: uuid.UUID
    platform: str
    section: str
    payload: dict[str, Any]
    current_version: int
    updated_at: datetime


class ContentPatch(BaseModel):
    platform: Platform
    section: Section
    payload: dict[str, Any]


class VersionOut(ORM):
    id: uuid.UUID
    content_id: uuid.UUID
    platform: str | None = None
    section: str | None = None
    version_number: int
    payload: dict[str, Any]
    source: str
    generation_params: dict[str, Any] | None
    created_at: datetime


class ExportRequest(BaseModel):
    format: ExportFormat
    platforms: list[Platform] | None = None


class MetricCreate(BaseModel):
    metric_date: date
    impressions: int | None = Field(default=None, ge=0)
    reach: int | None = Field(default=None, ge=0)
    video_views: int | None = Field(default=None, ge=0)
    clicks: int | None = Field(default=None, ge=0)
    conversions: int | None = Field(default=None, ge=0)
    spend: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _sane(self):
        vals = [self.impressions, self.reach, self.video_views, self.clicks, self.conversions, self.spend, self.revenue]
        if all(v is None for v in vals):
            raise ValueError("Provide at least one metric value.")
        if self.clicks is not None and self.impressions is not None and self.clicks > self.impressions:
            raise ValueError("clicks cannot exceed impressions.")
        if self.reach is not None and self.impressions is not None and self.reach > self.impressions:
            raise ValueError("reach cannot exceed impressions.")
        return self


class MetricOut(ORM):
    id: uuid.UUID
    metric_date: date
    impressions: int | None
    reach: int | None
    video_views: int | None
    clicks: int | None
    conversions: int | None
    spend: float | None
    revenue: float | None
    source: str
    ctr: float | None = None
    conversion_rate: float | None = None
    cpc: float | None = None
    cpa: float | None = None
    roas: float | None = None
