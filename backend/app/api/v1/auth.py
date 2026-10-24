from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import audit, commit_or_conflict, get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import APIError
from app.core.ratelimit import auth_limit, limiter
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas.auth import ChangePasswordIn, LoginIn, ProfileUpdate, RegisterIn, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])
_DUMMY_HASH = hash_password("timing-equaliser")  # verified against when the email is unknown


def _set_cookie(response: Response, user: User) -> None:
    s = get_settings()
    response.set_cookie(
        s.cookie_name, create_access_token(str(user.id)), max_age=s.access_token_minutes * 60,
        httponly=True, secure=s.cookie_secure, samesite="lax", path="/",
    )


@router.post("/register", response_model=UserOut, status_code=201)
@limiter.limit(auth_limit)
def register(request: Request, payload: RegisterIn, response: Response, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == payload.email)):
        raise APIError(409, "email_taken", "An account with this email already exists.")
    user = User(email=payload.email, password_hash=hash_password(payload.password),
                display_name=payload.display_name.strip())
    db.add(user)
    commit_or_conflict(db, "An account with this email already exists.")
    audit(db, user.id, "user.register", "user", user.id)
    db.commit()
    _set_cookie(response, user)
    return user


@router.post("/login", response_model=UserOut)
@limiter.limit(auth_limit)
def login(request: Request, payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))
    ok = verify_password(payload.password, user.password_hash if user else _DUMMY_HASH)
    if not user or not ok or not user.is_active:
        raise APIError(401, "invalid_credentials", "Incorrect email or password.")
    audit(db, user.id, "user.login", "user", user.id)
    db.commit()
    _set_cookie(response, user)
    return user


@router.post("/logout", status_code=204)
def logout():
    resp = Response(status_code=204)
    resp.delete_cookie(get_settings().cookie_name, path="/")
    return resp


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserOut)
def update_me(payload: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.display_name = payload.display_name.strip()
    db.commit()
    return user


@router.post("/change-password", status_code=204)
@limiter.limit(auth_limit)
def change_password(request: Request, payload: ChangePasswordIn, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if not verify_password(payload.current_password, user.password_hash):
        raise APIError(400, "wrong_password", "Current password is incorrect.")
    user.password_hash = hash_password(payload.new_password)
    audit(db, user.id, "user.change_password", "user", user.id)
    db.commit()
    return Response(status_code=204)
