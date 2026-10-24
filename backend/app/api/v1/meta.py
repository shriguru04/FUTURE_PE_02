from fastapi import APIRouter, Depends

from app.ai.factory import is_configured
from app.api.deps import get_current_user
from app.core import constants as c
from app.core.config import get_settings
from app.models import User
from app.services.generation import load_platforms

router = APIRouter(tags=["meta"])


@router.get("/meta")
def meta(_: User = Depends(get_current_user)):
    s = get_settings()
    cfg = load_platforms()
    return {
        "platforms": cfg["platforms"], "universal_checklist": cfg["universal_checklist"],
        "content_formats": list(c.CONTENT_FORMATS), "statuses": list(c.STATUSES), "sections": list(c.SECTIONS),
        "llm": {"configured": is_configured(s), "provider": s.llm_provider, "model": s.llm_model,
                "is_mock": s.llm_provider == "mock"},
    }
