SHELL := /bin/bash

.PHONY: up down dev logs test lint format migrate migration backup clean

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

lint:
	cd backend && ruff check .

format:
	cd backend && ruff format .

migrate:
	cd backend && alembic upgrade head

migration:
	cd backend && alembic revision --autogenerate -m '$(name)'

backup:
	bash scripts/backup_db.sh

clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf frontend/node_modules
