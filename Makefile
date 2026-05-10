SHELL := /bin/sh
COMPOSE := docker compose

.PHONY: help infra-up infra-down infra-logs infra-check compose-config backend-dev worker-dev frontend-dev

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
