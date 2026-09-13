.PHONY: help up down restart build logs ps clean migrate test

help:
	@echo "TARANG Platform Management Commands:"
	@echo "  make up        - Start all services with Docker Compose"
	@echo "  make down      - Stop all running services"
	@echo "  make restart   - Restart all services"
	@echo "  make build     - Rebuild Docker images for all services"
	@echo "  make logs      - View logs from all services"
	@echo "  make ps        - List all service container statuses"
	@echo "  make migrate   - Run Alembic database migrations"
	@echo "  make test      - Run test suites across services"
	@echo "  make clean     - Clean up build artifacts and temporary files"

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

build:
	docker compose build

logs:
	docker compose logs -f

ps:
	docker compose ps

migrate:
	docker compose exec backend-app alembic upgrade head

test:
	docker compose exec backend-app pytest
	docker compose exec frontend npm test

clean:
	docker compose down -v --remove-orphans
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
