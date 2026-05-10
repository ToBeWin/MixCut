SHELL := /bin/sh
COMPOSE := docker compose

.PHONY: help infra-up infra-down infra-logs infra-check compose-config backend-dev worker-dev frontend-dev lint test docker-build ci

help:
	@printf "%s\n" "MixCut developer commands"
	@printf "%s\n" "  make infra-up        Start local infrastructure"
	@printf "%s\n" "  make infra-down      Stop local infrastructure"
	@printf "%s\n" "  make infra-logs      Follow infrastructure logs"
	@printf "%s\n" "  make infra-check     Check local service endpoints"
	@printf "%s\n" "  make compose-config  Validate Compose files"
	@printf "%s\n" "  make backend-dev     Run FastAPI when backend/ exists"
	@printf "%s\n" "  make worker-dev      Run Celery worker when backend/ exists"
	@printf "%s\n" "  make frontend-dev    Run Next.js when frontend/ exists"
	@printf "%s\n" "  make lint            Run all linters (ruff + tsc)"
	@printf "%s\n" "  make test            Run all tests (backend + frontend)"
	@printf "%s\n" "  make docker-build    Build all Docker images"
	@printf "%s\n" "  make ci              Run full CI locally (lint + test)"

infra-up:
	$(COMPOSE) up -d postgres redis minio minio-init jaeger prometheus grafana

infra-down:
	$(COMPOSE) down

infra-logs:
	$(COMPOSE) logs -f postgres redis minio jaeger prometheus grafana

infra-check:
	./scripts/check-infra.sh

compose-config:
	$(COMPOSE) config >/dev/null
	$(COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml --profile app config >/dev/null

backend-dev:
	@test -d backend || (printf "%s\n" "backend/ is not present yet." >&2; exit 1)
	uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

worker-dev:
	@test -d backend || (printf "%s\n" "backend/ is not present yet." >&2; exit 1)
	celery -A backend.workers.tasks worker --loglevel=INFO --concurrency=1

frontend-dev:
	@test -d frontend || (printf "%s\n" "frontend/ is not present yet." >&2; exit 1)
	cd frontend && npm run dev

lint:
	@printf "%s\n" "=== Backend lint (ruff) ==="
	cd backend && ruff check .
	@printf "%s\n" "=== Frontend typecheck (tsc) ==="
	cd frontend && npm run typecheck
	@printf "%s\n" "=== All linting passed ==="

test:
	@printf "%s\n" "=== Backend tests ==="
	cd backend && python -m pytest tests/ services/ -v --tb=short
	@printf "%s\n" "=== Frontend tests ==="
	cd frontend && npm test -- --watchAll=false
	@printf "%s\n" "=== All tests passed ==="

docker-build:
	@printf "%s\n" "=== Building backend image ==="
	docker build -t mixcut-api:latest backend/
	@printf "%s\n" "=== Building frontend image ==="
	docker build -t mixcut-frontend:latest frontend/
	@printf "%s\n" "=== All images built ==="

ci: lint test
	@printf "%s\n" "=== CI passed ==="
