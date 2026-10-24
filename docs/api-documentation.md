# API contract (/api/v1) — errors: `{"error": {"code": str, "message": str, "details": any}}`

Auth: POST /auth/register, /auth/login (sets cookie), /auth/logout; GET /auth/me
Brands / Products: GET list (page, page_size, q), POST, GET /{id}, PATCH /{id}, DELETE /{id}
Campaigns: GET (page, page_size, q, status, platform), POST, GET/PATCH/DELETE /{id}, POST /{id}/duplicate
Generation: POST /campaigns/{id}/generate {platforms[], num_hooks, num_variations, ...}; POST /campaigns/{id}/regenerate-section {section, platform, instruction?}
Content: GET /campaigns/{id}/content?platform=; PATCH /campaigns/{id}/content {section, platform, payload}
Versions: GET /campaigns/{id}/versions?section=&platform=; POST /campaigns/{id}/versions/{vid}/restore
Export: POST /campaigns/{id}/export {format: txt|md|json|pdf, platforms?}
Analytics: GET /analytics/overview; GET /campaigns/{id}/analytics; POST /campaigns/{id}/metrics; GET /health (unversioned)

Status codes: 401 unauthenticated, 404 not found OR not yours, 409 conflict, 422 validation, 429 rate-limited, 502 LLM provider failure, 503 provider not configured.
