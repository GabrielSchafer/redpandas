PYTHON ?= python3
export PYTHONPATH := src

hooks:
	git config core.hooksPath .githooks

up:
	docker compose up -d

down:
	docker compose down -v

topics:
	$(PYTHON) scripts/create_topics.py

api:
	$(PYTHON) -m uvicorn trading.api.app:app --reload --port 8000

worker-ledger:
	$(PYTHON) -m trading.workers ledger

worker-risk:
	$(PYTHON) -m trading.workers risk

worker-matching:
	$(PYTHON) -m trading.workers matching

seed:
	$(PYTHON) scripts/seed.py

test:
	$(PYTHON) -m pytest -q

.PHONY: hooks up down topics api worker-ledger worker-risk worker-matching seed test
