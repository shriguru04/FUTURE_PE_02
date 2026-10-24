import uuid
from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import APIError

M = TypeVar("M")


def like_pattern(q: str) -> str:
    q = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{q}%"


class OwnedRepo(Generic[M]):
    """Every query is scoped by user_id. There is no unscoped accessor, so cross-user reads cannot be written by accident."""

    def __init__(self, model: type[M], db: Session, user_id: uuid.UUID):
        self.model, self.db, self.user_id = model, db, user_id

    def _scoped(self):
        return select(self.model).where(self.model.user_id == self.user_id)

    def get(self, id_: uuid.UUID) -> M | None:
        return self.db.scalar(self._scoped().where(self.model.id == id_))

    def get_or_404(self, id_: uuid.UUID, label: str = "Resource") -> M:
        obj = self.get(id_)
        if obj is None:  # same response whether it doesn't exist or belongs to someone else
            raise APIError(404, "not_found", f"{label} not found.")
        return obj

    def first(self, *filters) -> M | None:
        return self.db.scalar(self._scoped().where(*filters).limit(1))

    def list(self, *filters, order_by, page: int = 1, page_size: int = 20) -> tuple[list[M], int]:
        base = self._scoped().where(*filters)
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = self.db.scalars(
            base.order_by(*(order_by if isinstance(order_by, (list, tuple)) else [order_by]))
            .offset((page - 1) * page_size).limit(page_size)
        ).all()
        return list(items), total

    def count(self, *filters) -> int:
        return self.db.scalar(select(func.count()).select_from(self._scoped().where(*filters).subquery())) or 0
