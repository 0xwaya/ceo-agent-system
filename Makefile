.PHONY: consistency smoke test

PYTHON := python3

consistency:
	$(PYTHON) tools/enforce_consistency_gate.py

smoke:
	$(PYTHON) tools/smoke_dashboard_render.py

test:
	$(PYTHON) -m pytest -q
