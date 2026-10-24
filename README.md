# AdCraft AI

AI-powered UGC advertising platform: brands and products -> campaigns -> structured campaign packs (hooks, scene-by-scene scripts, captions, CTAs, hashtags, platform adaptations, claims review) -> editable, versioned, exportable.

**Stack:** React + Vite + TypeScript + Tailwind | FastAPI + SQLAlchemy 2 + Alembic | PostgreSQL | any OpenAI-compatible LLM (OpenAI GPT, xAI Grok, Ollama/vLLM) | Docker Compose.

> **Status honesty:** see [Verification status](#verification-status). Parts of this repository were written without the ability to run them. Run the test suites below before trusting anything.

## Quick start (Docker)

```bash
cp .env.example .env
# edit .env: set POSTGRES_PASSWORD, SECRET_KEY, and your LLM_* settings
docker compose up --build
# open http://localhost:8080   (API docs: http://localhost:8080/api/v1/... via UI; OpenAPI at the backend /docs when run directly)
```
Register an account, create a brand + product, create a campaign, click Generate.

**No API key yet?** Set `LLM_PROVIDER=mock` in `.env` (development only). The UI shows a "MOCK output" banner and generated text is labelled `[MOCK PROVIDER OUTPUT]`. It is refused when `APP_ENV=production`. With no provider configured, generation returns a clear 503 setup message and nothing is fabricated.

### Choosing GPT or Grok
Both are OpenAI-compatible; only three variables change:

| Provider | `LLM_BASE_URL` | `LLM_MODEL` |
|---|---|---|
| OpenAI GPT | `https://api.openai.com/v1` | e.g. `gpt-4o-mini` |
| xAI Grok | `https://api.x.ai/v1` | a current Grok model name from xAI's docs |
| Local (Ollama) | `http://host.docker.internal:11434/v1` | e.g. `llama3.1` (no key) |

Free-tier availability and quotas change; check the provider's current terms. Output is always validated server-side; weaker models may need more retries.

## Local development (no Docker)

```bash
# backend (Python 3.12)
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env        # DATABASE_URL defaults to local SQLite: sqlite:///./adcraft.db
alembic upgrade head
uvicorn app.main:app --reload  # http://localhost:8000/docs

# frontend (Node 20+)
cd frontend && npm install && npm run dev   # http://localhost:5173 (proxies /api to :8000)
```

## Tests

```bash
cd backend && pytest -q                                   # unit + API integration (SQLite temp DB, mock LLM, no network/paid calls)
TEST_DATABASE_URL=postgresql+psycopg://adcraft:pw@localhost:5432/adcraft_test pytest -q   # same suite on PostgreSQL (recommended before release)
cd frontend && npm test                                   # vitest: form validation + helpers
cd frontend && npm run typecheck                          # tsc --noEmit
```
Covers: registration/login/auth failures, cross-user isolation on every endpoint, brand/product/campaign CRUD, request validation, malformed AI output + retries, provider failure handling, versioning + restore, export authorization/formats, analytics math + zero denominators, DB constraints, the Alembic migration vs. the ORM models, and an API-level end-to-end journey (`tests/test_e2e_flow.py`). **Browser E2E (Playwright/Cypress) is not included.**

## Project layout

```
backend/app/{api/v1,core,models,schemas,repositories,services,ai,exports,config}  backend/alembic  backend/tests
frontend/src/{components,pages,layouts,hooks,services,context,utils,tests}
docs/{architecture,database-schema,api-documentation,security,deployment}.md
docker-compose.yml  .env.example
```

## Verification status

Executed in the authoring sandbox (no network, no Docker, no PostgreSQL, no FastAPI/SQLAlchemy/pytest installed):
- `python -m py_compile` on every backend module and test: pass.
- 9 dependency-free tests (`backend/tests/test_pure_logic.py`: analytics math incl. zero denominators, JSON extraction, hashtag normalisation, prompt sanitising, claim review, TXT/MD/JSON/PDF rendering, mock provider) were run with a stand-in runner: 9 passed.

**NOT executed (written but unverified):** the rest of the pytest suite (auth, CRUD, isolation, generation, versions, export API, DB constraints, migration test), the FastAPI app itself, the Alembic migration, all frontend code (`tsc`, `vite build`, vitest), Docker images and `docker compose up`, and any real LLM call. Expect to fix small issues on first run. Acceptance criteria 13-15 (tests green, Docker verified, a new developer can follow this README) are therefore **not yet demonstrated**.

## Known limitations
Manual analytics only (no platform integrations, no CSV import); synchronous generation; in-memory rate limiting; no refresh tokens or password reset; Latin-only PDF text. Details in [docs/security.md](docs/security.md).

## Deployment
See [docs/deployment.md](docs/deployment.md).
