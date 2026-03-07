.PHONY: up down logs test lint migrate seed trigger-product trigger-stock trigger-sales trigger-branches

up:
	docker compose up --build -d

down:
	docker compose down -v

logs:
	docker compose logs -f app worker mock-bsale-api

migrate:
	docker compose run --rm app alembic upgrade head

seed:
	docker compose run --rm app python scripts/seed_data.py

test:
	pytest -q

trigger-product:
	curl -X POST http://localhost:8000/admin/jobs/1/runs

trigger-stock:
	curl -X POST http://localhost:8000/admin/jobs/2/runs

trigger-sales:
	curl -X POST http://localhost:8000/admin/jobs/3/runs

trigger-branches:
	curl -X POST http://localhost:8000/admin/jobs/4/runs
