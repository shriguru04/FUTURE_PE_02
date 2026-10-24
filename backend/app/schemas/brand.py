from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import Long, Name, Short, TermList, Timestamps
import uuid


def _check_url(v):
    if v and not (v.startswith("http://") or v.startswith("https://")):
        raise ValueError("must start with http:// or https://")
    return v


class BrandCreate(BaseModel):
    name: Name
    category: Short = ""
    description: Long = ""
    target_audience: Long = ""
    voice: Short = ""
    language: Short = "English"
    writing_style: Short = ""
    messaging_guidelines: Long = ""
    avoid_terms: TermList = []
    website_url: Short = ""
    default_cta: Short = ""

    _url = field_validator("website_url")(_check_url)


class BrandUpdate(BaseModel):
    name: Name | None = None
    category: Short | None = None
    description: Long | None = None
    target_audience: Long | None = None
    voice: Short | None = None
    language: Short | None = None
    writing_style: Short | None = None
    messaging_guidelines: Long | None = None
    avoid_terms: TermList | None = None
    website_url: Short | None = None
    default_cta: Short | None = None

    _url = field_validator("website_url")(_check_url)


class BrandOut(Timestamps):
    name: str
    category: str
    description: str
    target_audience: str
    voice: str
    language: str
    writing_style: str
    messaging_guidelines: str
    avoid_terms: list[str]
    website_url: str
    default_cta: str


class ProductCreate(BaseModel):
    brand_id: uuid.UUID
    name: Name
    description: Long = ""
    features: TermList = []
    benefits: TermList = []
    price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    intended_audience: Long = ""
    supported_claims: TermList = []
    limitations: Long = ""
    offer_details: Long = ""
    cta: Short = ""


class ProductUpdate(BaseModel):
    name: Name | None = None
    description: Long | None = None
    features: TermList | None = None
    benefits: TermList | None = None
    price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    intended_audience: Long | None = None
    supported_claims: TermList | None = None
    limitations: Long | None = None
    offer_details: Long | None = None
    cta: Short | None = None


class ProductOut(Timestamps):
    brand_id: uuid.UUID
    name: str
    description: str
    features: list[str]
    benefits: list[str]
    price: float | None
    intended_audience: str
    supported_claims: list[str]
    limitations: str
    offer_details: str
    cta: str

    @field_validator("price", mode="before")
    @classmethod
    def _to_float(cls, v):
        return None if v is None else float(v)
