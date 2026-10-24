# AdCraft AI — Architecture (Phase 1)

Modular monolith: React/Vite (TypeScript) -> FastAPI -> PostgreSQL. No microservices.

## Key decisions (and the trade-off of each)

| Decision | Choice | Trade-off |
|---|---|---|
| LLM provider | ONE OpenAI-compatible adapter, configured by env: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`. Works for OpenAI GPT (`https://api.openai.com/v1`), xAI Grok (`https://api.x.ai/v1`), and local servers (Ollama/vLLM). A `MockProvider` is used in tests only. | Provider-specific features (native schemas, tool calls) are not used. Output is validated by Pydantic regardless. |
| Free tier | Not assumed. Check current OpenAI/xAI pricing and quotas before relying on either. | Without a funded key, generation returns a clear "provider not configured/failed" error. No fake content. |
| Auth | JWT in an httpOnly, SameSite=Lax cookie, 60 min expiry, Argon2 hashing. State-changing requests also checked against an allowed-Origin list. | No refresh tokens in v1: users re-login hourly. Cookies avoid XSS token theft but need CORS `allow_credentials` and CSRF care. |
| Generation | Synchronous request (timeout 90s), each call recorded in `generation_jobs`. | A reverse proxy with a short timeout will break it. Async job + polling is the next step if needed. |
| Rate limiting | `slowapi`, in-memory. | Not shared across multiple API instances. Needs Redis in multi-instance production. |
| PDF export | `reportlab` (pure Python). | Plainer layout than HTML->PDF, but no system libraries in Docker. |
| Platform rules | `backend/app/config/platforms.json`, editable, never claimed as current policy. | Guidelines can go stale; the UI shows a pre-publish checklist, not a compliance verdict. |
| JSON columns | JSONB only for `payload`/`generation_params`. Core entities use real columns. | JSONB on SQLite needs a JSON variant; Postgres-only behavior must be tested on Postgres. |

## Layers (backend/app)
`api/` routers -> `services/` business logic -> `repositories/` queries (always scoped by `user_id`) -> `models/`.
`ai/`: `base.py` (Provider interface), `openai_compat.py`, `mock.py`, `prompts/`, `schemas.py` (Pydantic output), `generator.py` (retry + validation).
`exports/`: txt, md, json, pdf. `core/`: config, security, logging (redacts secrets), rate limits.

## Generation flow
1. Load campaign, brand, product (ownership checked).
2. Snapshot product/brand context into `generation_params` (so later product edits don't rewrite history).
3. Render prompt template. Reference content is wrapped as untrusted data, never as instructions.
4. Provider call: timeout, max 2 retries on 429/5xx/timeouts, 2 retries on schema-invalid output (feeding validation errors back).
5. Validate with Pydantic. Run claims review: any claim not in the product's `supported_claims` is flagged.
6. Save new `content_versions` rows, update `campaign_contents`. All in one DB transaction.

## Security notes
Every user-owned table has `user_id`. Repositories take `user_id` as a required argument, so an unscoped query is not expressible. Cross-user access returns 404, not 403. Logs redact `Authorization`, cookies, API keys, passwords.
