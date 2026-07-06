# Contributing to galley

## Dev Environment

Prerequisites: Docker, [uv](https://docs.astral.sh/uv/), Node.js 18+

```bash
git clone https://github.com/zrd/galley.git
cd galley

cp .env.example .env
make setup   # starts Postgres, runs migrations
make run     # backend at http://localhost:8000

cd frontend
npm install
cp .env.example .env
npm run dev  # frontend at http://localhost:5173
```

## Make Targets

| Target | What it does |
|--------|-------------|
| `make setup` | Start Postgres and run all migrations |
| `make run` | Start the backend (uvicorn, hot reload) |
| `make test` | Run the test suite |
| `make lint` | Run ruff |
| `make db-up` | Start Postgres only |
| `make db-down` | Stop Postgres |
| `make db-migrate` | Apply pending migrations |
| `make db-revision m="…"` | Generate a new migration |
| `make db-reset` | Drop the volume and restart Postgres (data loss) |

## Running the Tests

```bash
make test
```

Tests require the database to be running (`make db-up`).

## Branches and PRs

- Branch names follow the ticket ID: `STORE-012`, `BUG-007`, etc.
- One ticket per branch; merge to `main` when done
- Keep commits focused — a commit should leave the tests green

## Opening Issues

Use GitHub Issues. Bug reports should include steps to reproduce and what you expected to happen.

## License

By contributing you agree that your contributions will be licensed under the project's [AGPL-3.0 license](LICENSE).
