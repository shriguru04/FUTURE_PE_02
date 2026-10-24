import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import PageParams, apply_update, audit, commit_or_conflict, get_current_user, paginated
from app.core.database import get_db
from app.core.errors import APIError
from app.models import Brand, Product, User
from app.repositories.base import OwnedRepo, like_pattern
from app.schemas.brand import ProductCreate, ProductOut, ProductUpdate
from app.schemas.common import Page

router = APIRouter(prefix="/products", tags=["products"])
NON_NULL = {"name", "description", "features", "benefits", "intended_audience", "supported_claims",
            "limitations", "offer_details", "cta"}


@router.get("", response_model=Page[ProductOut])
def list_products(q: str | None = Query(None, max_length=100), brand_id: uuid.UUID | None = None,
                  p: PageParams = Depends(), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    filters = []
    if q:
        filters.append(Product.name.ilike(like_pattern(q), escape="\\"))
    if brand_id:
        filters.append(Product.brand_id == brand_id)
    items, total = OwnedRepo(Product, db, user.id).list(*filters, order_by=Product.name, page=p.page, page_size=p.page_size)
    return paginated(items, total, p)


@router.post("", response_model=ProductOut, status_code=201)
def create_product(payload: ProductCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    OwnedRepo(Brand, db, user.id).get_or_404(payload.brand_id, "Brand")
    if OwnedRepo(Product, db, user.id).first(Product.brand_id == payload.brand_id, Product.name == payload.name):
        raise APIError(409, "product_exists", "This brand already has a product with this name.")
    product = Product(user_id=user.id, **payload.model_dump())
    db.add(product)
    commit_or_conflict(db, "This brand already has a product with this name.")
    return product


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return OwnedRepo(Product, db, user.id).get_or_404(product_id, "Product")


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(product_id: uuid.UUID, payload: ProductUpdate, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    repo = OwnedRepo(Product, db, user.id)
    product = repo.get_or_404(product_id, "Product")
    data = payload.model_dump(exclude_unset=True)
    if data.get("name") and repo.first(Product.brand_id == product.brand_id, Product.name == data["name"],
                                        Product.id != product.id):
        raise APIError(409, "product_exists", "This brand already has a product with this name.")
    apply_update(product, data, NON_NULL)
    commit_or_conflict(db, "This brand already has a product with this name.")
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    product = OwnedRepo(Product, db, user.id).get_or_404(product_id, "Product")
    db.delete(product)  # campaigns keep existing; their product_id becomes NULL (ON DELETE SET NULL)
    audit(db, user.id, "product.delete", "product", product_id)
    db.commit()
    return Response(status_code=204)
