import uuid

from fastapi import Depends, Query, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai.base import LLMProvider, ProviderNotConfigured
from app.ai.factory import build_provider
from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import APIError
from app.core.security import decode_access_token
from app.models import AuditEvent, User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    s = get_settings()
    token = request.cookies.get(s.cookie_name)
    if not token:
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth[7:].strip()
    if not token:
        raise APIError(401, "not_authenticated", "Authentication required.")
    sub = decode_access_token(token)
    try:
        uid = uuid.UUID(sub) if sub else None
    except ValueError:
        uid = None
    user = db.get(User, uid) if uid else None
    if user is None or not user.is_active:
        raise APIError(401, "invalid_token", "Your session is invalid or expired. Please log in again.")
    return user


def get_provider() -> LLMProvider:
    try:
        return build_provider(get_settings())
    except ProviderNotConfigured as exc:
        raise APIError(503, "provider_not_configured", exc.message) from exc


class PageParams:
    def __init__(self, page: int = Query(1, ge=1, le=10000), page_size: int = Query(20, ge=1, le=100)):
        self.page, self.page_size = page, page_size


def paginated(items, total: int, p: PageParams) -> dict:
    return {"items": items, "total": total, "page": p.page, "page_size": p.page_size}


def commit_or_conflict(db: Session, message: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise APIError(409, "conflict", message) from exc


def apply_update(obj, data: dict, non_nullable: set[str]) -> None:
    for k, v in data.items():
        if v is None and k in non_nullable:
            raise APIError(422, "validation_error", f"'{k}' cannot be null.")
        setattr(obj, k, v)


def audit(db: Session, user_id, action: str, entity_type: str = "", entity_id="") -> None:
    db.add(AuditEvent(user_id=user_id, action=action, entity_type=entity_type, entity_id=str(entity_id)))
