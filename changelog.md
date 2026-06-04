# Study Smart — Changelog

## [Unreleased]

### 2026-06-04: "ACID" Redesign & Production Hardening

- **Redesign**: New dark "ACID" theme (lime accent, Unbounded/Manrope/JetBrains Mono)
  ported across all templates via a plain-CSS design system; HTMX/Alpine/i18n preserved.
- **Security**: Env-driven `CSRF_TRUSTED_ORIGINS`; `SECURE_SSL_REDIRECT` + HSTS + secure
  cookies; `X_FRAME_OPTIONS=DENY`; hardened `sanitize_html` (URL-scheme allowlist, no `target`);
  required `DATABASE_PASSWORD`/`EMAIL_HOST`; request/upload size limits.
- **Payments**: Atomic, idempotent Stripe webhook (retry on failure); `past_due` grace +
  downgrade on terminal statuses; `invoice.payment_failed` handling.
- **Quota/AI/Auth**: Atomic usage consume (advisory lock) closing the limit race; AI provider
  timeouts + Celery `soft_time_limit`/retry; migrated `google-generativeai` → `google-genai`;
  atomic single-use magic link resolving accounts by email; login/registration throttling.
- **Static/Perf**: WhiteNoise compressed + hashed static (cache-busting); pinned CDN versions;
  optimized logo assets; meta description + favicon; fixed a console JS error.
- **Infra/Quality**: Pinned dependencies + prod/dev split; GitHub Actions CI; env-gated Redis
  cache; `LOGGING` config; Sentry sample rates from env; DB indexes on `Prompt`; removed dead
  files; `DEPLOYMENT.md` runbook. Test suite expanded to 89 tests.
- **i18n**: Launch on RU + EN (DE/FR/ES hidden until translated); dynamic `<html lang>`.

### 2026-02-09: Guest Experience & Localization

- **Guest Access**: Enabled settings configuration for unregistered users (stored in session).
- **UI Improvements**: Added guest settings link in header and notification banner on home page.
- **Localization**: Fixed missing translations for "Login to purchase" and "Settings saved".
- **Fixes**: Resolved duplicate keys in PO files and updated GitHub link.

### 2026-02-09: Production Readiness & Stabilization

- **Fixed generation errors**: Switched Qwen to `qwen-turbo` (resolved 403), handled Gemini 429 quotas.
- **Unified UI**: Removed client-side skeleton loader, standardized loading state across all views to use server-side rendering.
- **Localization**: Added missing translations for page titles, error messages, and loading indicators (RU, FR, ES).
- **Infrastructure**: Integrated Sentry for error monitoring.
- **DevOps**: Fixed Docker build issues and optimized container restart flow.

### 2026-02-09: Code Stabilization & Type Hinting

- Renamed `mock_generate_sections` to `generate_sections` in `apps/prompts/services.py` (removed misleading naming)
- Added Type Hints to `apps/core/utils.py` and `apps/core/mixins.py`
- Added Type Hints to `apps/prompts/services.py` and `apps/prompts/views.py`
- Verified functionality with `pytest` (62/62 passed)

### 2026-02-09: Project Cleanup & Ownership Refactoring

- Removed junk files from project root (nul, fix_section.py, test_gemini.py, .coverage, PROJECT_ANALYSIS.md)
- Created `.gitignore` with Python/Django/Docker/IDE rules
- Cleaned all `__pycache__` directories
- Added `README.md` (English)
- Extracted ownership utilities into `apps/core/utils.py`: `ensure_session`, `get_owner_filter`, `check_ownership`, `get_user_settings`
- Added `OwnershipMixin` to `apps/core/mixins.py` for class-based views
- Refactored `apps/prompts/views.py` — replaced 5 duplicated user/session checks with utility calls
- Refactored `apps/history/views.py` — replaced 4 duplicated ownership checks with utility calls and mixin
- Refactored `apps/settings_app/views.py` — replaced 24-line settings loader with single `get_user_settings()` call

### 2026-02-08: Rate Limiting & Subscription System

- Added `apps/subscriptions` application
- Implemented subscription plans: Guest, Free, Pro, Pro+
- Added usage tracking and rate limiting for AI requests
- Guest: 5 requests/month
- Free: 10 requests/week
- Pro: 50 requests/day (€15/month)
- Pro+: 200 requests/day (€40/month)

---

## Previous Changes

### Docker Configuration

- Multi-stage Dockerfile
- Docker Compose with web, db, nginx services
- PostgreSQL integration

### Localization

- i18n support for ru, en, de
- Language switcher in header

### Core Features

- AI-powered study assistance
- Magic link authentication
- User settings persistence
- History tracking
