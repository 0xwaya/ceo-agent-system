.PHONY: consistency smoke test lint format-check check

PYTHON := python3

consistency:
	$(PYTHON) tools/enforce_consistency_gate.py

smoke:
	$(PYTHON) tools/smoke_dashboard_render.py

test:
	$(PYTHON) -m pytest -q

format-check:
	$(PYTHON) -m black --check . --line-length 100

lint:
	$(PYTHON) -m flake8 . --max-line-length=100 --exclude=.git,.venv,venv,__pycache__

check: format-check lint consistency smoke test
