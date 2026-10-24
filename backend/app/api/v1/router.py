from fastapi import APIRouter

from app.api.v1 import analytics, auth, brands, campaigns, content, exports, generation, meta, products

api_router = APIRouter(prefix="/api/v1")
for module in (auth, meta, brands, products, campaigns, generation, content, exports, analytics):
    api_router.include_router(module.router)
