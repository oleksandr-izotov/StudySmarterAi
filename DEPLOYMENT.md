# Deployment Runbook — Study Smart

Production deployment with Docker Compose (web + Celery worker + PostgreSQL +
Redis + nginx). This is the source of truth for taking the app live.

---

## 1. Prerequisites

- Docker + Docker Compose on the host
- A domain pointing at the host, with TLS terminated in front (nginx/Caddy/ALB).
  The app sets `SECURE_SSL_REDIRECT` + HSTS and trusts `X-Forwarded-Proto`.
- API keys: Google Gemini (required), Qwen/DashScope (optional fallback), Stripe.
- An SMTP account (magic-link login sends real email in production).

## 2. Configure environment

```bash
cp .env.example .env
```

Fill in `.env`. **Required** (the app fails fast if these are missing):

| Var | Notes |
|---|---|
| `SECRET_KEY` | Long random string. Generate: `python -c "import secrets;print(secrets.token_urlsafe(64))"` |
| `DEBUG` | `False` in production |
| `ALLOWED_HOSTS` | e.g. `studyai.app,www.studyai.app` |
| `CSRF_TRUSTED_ORIGINS` | Your real **https** origins, e.g. `https://studyai.app,https://www.studyai.app` |
| `DATABASE_PASSWORD` | Strong password (no default — compose refuses to start without it) |
| `GEMINI_API_KEY` | Google Gemini key |
| `EMAIL_HOST` (+ `EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD`) | SMTP — required when `DEBUG=False` |
| `STRIPE_SECRET_KEY`, `STRIPE_PUBLIC_KEY`, `STRIPE_WEBHOOK_SECRET` | Stripe live keys + webhook signing secret |

Useful **optional** vars: `QWEN_API_KEY`, `REDIS_CACHE_URL` (shared rate-limit
cache across workers), `SENTRY_DSN`, `SECURE_HSTS_SECONDS`, `LOG_LEVEL`,
`SECURE_SSL_REDIRECT`. See `.env.example` for the full list.

> **First deploy on a fresh domain:** set `SECURE_HSTS_SECONDS=0` for the very
> first rollout, confirm HTTPS works end-to-end, then raise it (e.g. `31536000`).
> HSTS pins browsers to HTTPS and is hard to undo.

## 3. Build & start

```bash
docker compose up --build -d
```

On startup the `web` container entrypoint automatically:
1. waits for the database,
2. runs `migrate`,
3. runs `collectstatic` (hashed + compressed via WhiteNoise),
4. runs `compilemessages`,
5. runs `init_plans` (seeds Guest/Free/Pro/Pro+ subscription plans).

The app is served by nginx on **http://&lt;host&gt;:8080** (container port 80).
Put your TLS proxy in front of that.

## 4. One-time setup

```bash
# Admin user
docker compose exec web python manage.py createsuperuser

# Stripe price IDs must be attached to the plans (Pro / Pro+) before checkout
# works. Set them in the DB (admin → Subscription plans → stripe_price_id) or via
# a management command, matching the Stripe products you created.
```

**Stripe webhook:** in the Stripe dashboard add an endpoint
`https://<your-domain>/subscriptions/webhook/` subscribed to:
`checkout.session.completed`, `customer.subscription.updated`,
`customer.subscription.deleted`, `invoice.payment_failed`. Copy its signing
secret into `STRIPE_WEBHOOK_SECRET` and restart.

## 5. Health & logs

- Health endpoint: `/health/` (used by the compose healthchecks).
- Logs: `docker compose logs -f web` (and `worker`, `nginx`). App logs to stdout.

## 6. Updating

```bash
git pull
docker compose up --build -d   # entrypoint re-runs migrate/collectstatic/compilemessages
```

Migrations and static collection run automatically on container start.

## 7. Backups

- Database volume: `study_smart_postgres`. Dump regularly:
  ```bash
  docker compose exec db pg_dump -U "$DATABASE_USER" "$DATABASE_NAME" > backup.sql
  ```
- Uploaded media volume: `study_smart_media`.

## 8. Running tests (CI parity)

```bash
docker compose --profile test run --rm test
```
CI (GitHub Actions) runs the same suite on every push/PR.

---

## Notes / caveats

- **UI languages** currently launch on **RU + EN**. German/French/Spanish
  translations exist in `locale/` but are hidden from the switcher until
  completed; re-enable by adding them back to `LANGUAGES` in `config/settings.py`
  and finishing their `.po` files (run `makemessages` with GNU gettext).
- Static files use hashed filenames in production (cache-busting), so the nginx
  `immutable` cache header is safe.
