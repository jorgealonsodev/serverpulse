# Tasks: ServerPulse Fase 9 — CI/CD

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~420 (2 YAML workflow files + docs) |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Suggested split | Single PR acceptable — declarative YAML, self-contained |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | CI + Deploy workflows + docs | PR 1 | All files, self-contained; no code changes |

## Phase 1: CI Workflow

- [x] 1.1 Create `.github/workflows/ci.yml` with `on: [push, pull_request]` trigger
- [x] 1.2 Add `backend-lint` job: Python 3.12, `pip install -e ".[dev]"`, `ruff check .` + `ruff format --check`
- [x] 1.3 Add `backend-test` job: Python 3.12, service containers (postgres:16-alpine, redis:7-alpine), env vars (DATABASE_URL, REDIS_URL, JWT_SECRET), `pytest --cov=app`
- [x] 1.4 Add `frontend-lint` job: Node 20, `npm ci`, `tsc --noEmit`
- [x] 1.5 Add `frontend-test` job: Node 20, `npm ci`, `vitest run`
- [x] 1.6 Add `docker-build` job: build backend, frontend, nginx images without push

## Phase 2: Deploy Workflow

- [x] 2.1 Create `.github/workflows/deploy.yml` with `on: push to main` and `workflow_dispatch`
- [x] 2.2 Add `build-push` job: GHCR login, build + push backend/frontend/nginx with `latest` + `sha-{short}` tags
- [x] 2.3 Add `deploy` job: `appleboy/ssh-action@v1`, run pull + compose up + health check on `${{ secrets.DEPLOY_HOST }}`
- [x] 2.4 Implement rollback: store `PREV_SHA` before deploy; on health failure, SSH redeploy previous `sha-{short}` tag

## Phase 3: Docker Compose + Documentation

- [x] 3.1 Add `workflow_dispatch` to `docker-compose.yml` for manual trigger support
- [x] 3.2 Add `.github/workflows/` to `.gitignore` if not already excluded
- [x] 3.3 Create `docs/secrets.md` documenting required secrets: GHCR_TOKEN, DEPLOY_HOST, DEPLOY_USER, DEPLOY_KEY, JWT_SECRET (with example values for CI)