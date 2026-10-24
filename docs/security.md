# Security assumptions, trade-offs and hardening

Implemented: Argon2 password hashing; JWT in httpOnly + SameSite=Lax cookie (60 min, no refresh token); every repository query scoped by `user_id` and cross-user access returns 404; Origin check on unsafe methods (CSRF defence); CORS allow-list; rate limiting on auth and generation; Pydantic validation everywhere; DB CHECK/UNIQUE/FK constraints; log redaction of keys/tokens/passwords; generic 500s (no stack traces to clients); reference content is length-capped, control-char-stripped and fenced as untrusted in the prompt; mock provider refused when `APP_ENV=production`; startup refuses default `SECRET_KEY` / insecure cookies in production.

Known limitations (be aware before going live):
- **Rate limiting is in-memory** (slowapi). It is per API instance; use a Redis backend for multi-instance deployments. Behind a proxy, only trust forwarded headers from that proxy.
- **No refresh tokens / token revocation.** Logout clears the cookie but a stolen token stays valid until expiry. Changing the password does not invalidate existing tokens.
- **No email verification or password reset.**
- **Prompt injection cannot be fully prevented.** Fencing reduces risk; outputs are validated and claims are re-checked deterministically, but a human must review before publishing.
- **Claim review is advisory.** It flags claims that do not match the product's supported claims by simple text matching; it does not verify truth.
- **Platform guidelines** (`backend/app/config/platforms.json`) are editable starting points, not current policy.
- **PDF export** uses built-in Helvetica (Latin text only).
- **Analytics are manual entry only.** No Instagram/Facebook/YouTube integration exists. CSV import is not implemented (the `csv_import` source value is reserved).
- **Generation is synchronous** (up to ~90 s per platform); long proxy timeouts are required.
- **Audit events** are written for key actions but there is no UI to view them.
- **Account deletion** is not implemented.
- Pin and scan dependencies (`pip-audit`, `npm audit`) in CI.
