SHELL := /bin/bash

.PHONY: up down dev logs test lint format migrate migration backup clean frontend-dev frontend-test frontend-lint frontend-format

up:
	docker compose up -d

down:
	docker compose down

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

logs:
	docker compose logs -f

test:
	cd backend && pytest
	cd frontend && npm test

lint:
	cd backend && ruff check .
	cd frontend && npm run lint

format:
	cd backend && ruff format .
	cd frontend && npx prettier --write "src/**/*.{ts,tsx}"

migrate:
	cd backend && alembic upgrade head

migration:
	cd backend && alembic revision --autogenerate -m '$(name)'

backup:
	bash scripts/backup_db.sh

frontend-dev:
	cd frontend && npm run dev

frontend-test:
	cd frontend && npm test

frontend-lint:
	cd frontend && npm run lint

frontend-format:
	cd frontend && npx prettier --write "src/**/*.{ts,tsx}"

clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf frontend/node_modules frontend/dist
