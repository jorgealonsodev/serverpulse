SHELL := /bin/bash

.PHONY: up down dev logs test lint format migrate migration backup clean

up:
	@echo "TODO: implement in Fase 8 — docker compose up -d"

down:
	@echo "TODO: implement in Fase 8 — docker compose down"

dev:
	@echo "TODO: implement in Fase 8 — docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d"

logs:
	@echo "TODO: implement in Fase 8 — docker compose logs -f"

test:
	@echo "TODO: implement in Fase 1 — pytest backend/tests && cd frontend && vitest run"

lint:
	@echo "TODO: implement in Fase 1 — ruff check backend/ && cd frontend && eslint src/"

format:
	@echo "TODO: implement in Fase 1 — ruff format backend/ && cd frontend && prettier --write src/"

migrate:
	@echo "TODO: implement in Fase 1 — cd backend && alembic upgrade head"

migration:
	@echo "TODO: implement in Fase 1 — cd backend && alembic revision --autogenerate -m '$(name)'"

backup:
	@echo "TODO: implement in Fase 12 — bash scripts/backup_db.sh"

clean:
	@echo "TODO: implement in Fase 8 — docker compose down -v && find . -type d -name __pycache__ -exec rm -rf {} + && rm -rf frontend/node_modules"
