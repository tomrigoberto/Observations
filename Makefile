.PHONY: up build down logs reset backend-shell db-shell test library-tests seed-demo fmt

# Build then start. Split because Docker Compose v5 changed `up --build` semantics;
# `build` + `up -d` works on both v2 and v5.
up:
	docker compose build
	docker compose up -d

build:
	docker compose build

down:
	docker compose down

logs:
	docker compose logs -f

reset:
	docker compose down -v

backend-shell:
	docker compose exec backend bash

db-shell:
	docker compose exec postgres psql -U observations -d observations

test:
	docker compose exec backend pytest

library-tests:
	docker compose exec backend python -m app.engine.library_test_runner

seed-demo:
	docker compose exec backend python -m app.seed.demo

fmt:
	docker compose exec backend ruff format app/ && docker compose exec backend ruff check --fix app/
