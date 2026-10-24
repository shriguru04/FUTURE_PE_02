import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import PageParams, apply_update, audit, commit_or_conflict, get_current_user, paginated
from app.core.database import get_db
from app.core.errors import APIError
from app.models import Brand, Campaign, User
from app.repositories.base import OwnedRepo, like_pattern
from app.schemas.brand import BrandCreate, BrandOut, BrandUpdate
from app.schemas.common import Page

router = APIRouter(prefix="/brands", tags=["brands"])
NON_NULL = {"name", "category", "description", "target_audience", "voice", "language", "writing_style",
            "messaging_guidelines", "avoid_terms", "website_url", "default_cta"}


@router.get("", response_model=Page[BrandOut])
def list_brands(q: str | None = Query(None, max_length=100), p: PageParams = Depends(),
                user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    filters = [Brand.name.ilike(like_pattern(q), escape="\\")] if q else []
    items, total = OwnedRepo(Brand, db, user.id).list(*filters, order_by=Brand.name, page=p.page, page_size=p.page_size)
    return paginated(items, total, p)


@router.post("", response_model=BrandOut, status_code=201)
def create_brand(payload: BrandCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = OwnedRepo(Brand, db, user.id)
    if repo.first(Brand.name == payload.name):
        raise APIError(409, "brand_exists", "You already have a brand with this name.")
    brand = Brand(user_id=user.id, **payload.model_dump())
    db.add(brand)
    commit_or_conflict(db, "You already have a brand with this name.")
    return brand


@router.get("/{brand_id}", response_model=BrandOut)
def get_brand(brand_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return OwnedRepo(Brand, db, user.id).get_or_404(brand_id, "Brand")


@router.patch("/{brand_id}", response_model=BrandOut)
def update_brand(brand_id: uuid.UUID, payload: BrandUpdate, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    repo = OwnedRepo(Brand, db, user.id)
    brand = repo.get_or_404(brand_id, "Brand")
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] and repo.first(Brand.name == data["name"], Brand.id != brand.id):
        raise APIError(409, "brand_exists", "You already have a brand with this name.")
    apply_update(brand, data, NON_NULL)
    commit_or_conflict(db, "You already have a brand with this name.")
    return brand


@router.delete("/{brand_id}", status_code=204)
def delete_brand(brand_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    brand = OwnedRepo(Brand, db, user.id).get_or_404(brand_id, "Brand")
    if OwnedRepo(Campaign, db, user.id).count(Campaign.brand_id == brand.id):
        raise APIError(409, "brand_in_use", "This brand has campaigns. Delete or archive them first.")
    db.delete(brand)  # products are removed by ON DELETE CASCADE
    audit(db, user.id, "brand.delete", "brand", brand_id)
    commit_or_conflict(db, "This brand is still in use.")
    return Response(status_code=204)
