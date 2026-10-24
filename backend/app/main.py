import logging
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import engine
from app.core.errors import register_handlers
from app.core.logging import configure_logging
from app.core.ratelimit import limiter

settings = get_settings()
configure_logging(settings.log_level)
log = logging.getLogger("adcraft")

app = FastAPI(title="AdCraft AI API", version="1.0.0",
              description="AI-powered UGC content marketing platform. Generated content is a draft, not verified fact.")
app.state.limiter = limiter
register_handlers(app)

UNSAFE = {"POST", "PUT", "PATCH", "DELETE"}


@app.middleware("http")
async def origin_check(request: Request, call_next):
    """CSRF defence for cookie auth: browsers always send Origin on cross-site unsafe requests."""
    origin = request.headers.get("origin")
    if request.method in UNSAFE and origin:
        allowed = {o.rstrip("/") for o in settings.origins}
        same_host = urlparse(origin).netloc == request.headers.get("host", "")
        if origin.rstrip("/") not in allowed and not same_host:
            return JSONResponse({"error": {"code": "bad_origin", "message": "Origin not allowed.", "details": None}},
                                status_code=403)
    return await call_next(request)


app.add_middleware(SlowAPIMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True,
                   allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
                   allow_headers=["Content-Type", "Authorization"], expose_headers=["Content-Disposition"])
app.include_router(api_router)


@app.get("/health", tags=["meta"])
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        return JSONResponse({"status": "unhealthy", "database": False}, status_code=503)
    return {"status": "ok", "database": True}
