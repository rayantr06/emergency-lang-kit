# Repository Guidelines

Quick guardrails for contributing to Emergency Lang Kit (ELK). Favor small, typed changes with tests and minimal surface area.

## Project Structure & Module Organization
- `elk/api/`: FastAPI gateway (routes, schemas, middleware).
- `elk/workers/`: Arq worker entrypoint (`main.py`) for async jobs.
- `elk/engine/`, `elk/core/`: Kernel logic, configs, shared utilities.
- `elk/database/`: SQLModel models and session helpers.
- `elk/connectors/`: ERP/webhook adapters; keep external I/O isolated.
- `packs/`: Language/domain packs scaffolded via `elk/cli.py scaffold`.
- `docs/`, `examples/`, `tools/`, `tests/`: Docs, samples, helper scripts, and test suite.

## Build, Test, and Development Commands
- Install deps: `pip install -r requirements.txt` (add `requirements-dev.txt` for linting/typing).
- Run API: `uvicorn elk.api.app:app --reload --host 0.0.0.0 --port 8000`.
- Start worker: `arq elk.workers.main.WorkerSettings` (needs `REDIS_URL`).
- Compose stack: `docker-compose up --build` (API on `:8000`, worker + Redis bundled).
- Tests: `python -m pytest tests` or `-k pattern` for focus.
- Lint/format: `ruff check .` and `ruff format .`; `black .` acceptable locally.

## Coding Style & Naming Conventions
- Ruff config: line length 100, double quotes, spaces. Type hints expected; avoid `Any` unless justified.
- Prefer Enums over magic strings; keep Pydantic v2 `ConfigDict` patterns and explicit schemas.
- Modules/files/functions in `snake_case`; classes `PascalCase`; constants `UPPER_SNAKE_CASE`.
- Use structured logging over prints; keep connector logic side-effect free and testable.

## Testing Guidelines
- Pytest with files named `test_*.py`; mirror app modules where possible.
- Use `fastapi.testclient.TestClient` fixture (`tests/conftest.py`) for HTTP flows; prefer fixtures/factories over inline mocks.
- Cover happy and failure paths for API, workers, pack loaders; keep tests deterministic (no network calls).
- New packs/connectors should add contract-style checks for schema validation and job state updates.

## Commit & Pull Request Guidelines
- Commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`) with scopes like `schema`, `tests`, `package`.
- Before pushing: lint, format, and `python -m pytest tests`; update README/PRD/docs when interfaces or pack structure change.
- PRs need a brief summary, linked issue, testing notes, and screenshots/log snippets for API-visible changes.

## Security & Configuration Tips
- Copy `.env.example` to `.env`; never commit secrets (Gemini, Redis, DB URLs).
- Store generated artifacts locally (`logs/`, `packs/*/models`); avoid committing them. Validate inputs and sanitize connector outputs to prevent PII leakage.
