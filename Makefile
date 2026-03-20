.PHONY: run test lint db-up db-down db-migrate db-revision db-reset

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

# Scaffold a new migration (usage: make db-revision m="your message here")
# Auto-prefixes the file with the next sequential number (e.g. 006_add_tags.py)
# and updates revision/down_revision IDs inside the file to match.
db-revision:
	@set -e; \
	LAST=$$(ls alembic/versions/[0-9][0-9][0-9]_*.py 2>/dev/null | sed 's|.*/\([0-9]*\)_.*|\1|' | sort -n | tail -1); \
	NEXT=$$(printf "%03d" $$(( $${LAST:-0} + 1 ))); \
	NEW_FILE=$$(uv run alembic revision -m "$(m)" 2>&1 | grep "Generating" | awk '{print $$2}'); \
	SLUG=$$(basename "$$NEW_FILE" | sed 's/^[a-f0-9]*_//'); \
	TARGET="alembic/versions/$${NEXT}_$${SLUG}"; \
	mv "$$NEW_FILE" "$$TARGET"; \
	HEX=$$(grep "^revision" "$$TARGET" | grep -oE "[a-f0-9]{10,}" | head -1); \
	sed -i "s/$$HEX/$$NEXT/g" "$$TARGET"; \
	echo "Created $$TARGET"

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
