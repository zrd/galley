.PHONY: run test lint db-up db-down db-migrate db-reset

# Start the FastAPI server
run:
	uv run uvicorn app.main:app --reload

# Run tests
test:
	uv run pytest

# Run linter
lint:
	uv run ruff check .

# Start PostgreSQL container
db-up:
	docker compose up -d postgres
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 2
	@docker compose exec postgres pg_isready -U postgres -d self_publishing || (echo "Database not ready" && exit 1)
	@echo "PostgreSQL is ready!"

# Stop PostgreSQL container
db-down:
	docker compose down

# Run database migrations
db-migrate:
	uv run alembic upgrade head

# Reset database (destroy and recreate)
db-reset:
	docker compose down -v
	docker compose up -d postgres
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 3
	uv run alembic upgrade head

# Setup everything for development
setup: db-up db-migrate
	@echo "Development environment ready!"
	@echo "Run 'make run' to start the server"
