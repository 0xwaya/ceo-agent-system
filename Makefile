.PHONY: consistency smoke test

consistency:
	python3 tools/enforce_consistency_gate.py

smoke:
	python3 tools/smoke_dashboard_render.py

test:
	pytest -q
