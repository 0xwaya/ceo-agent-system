#!/usr/bin/env python3
"""Quick smoke checks for dashboard rendering under development and production.

Checks:
- /graph route renders and includes graph config bootstrap
- /admin route renders and includes admin config bootstrap
- Legacy index template (index.html) renders directly with scenario defaults

This script does not start a browser server; it validates rendered HTML quickly via Flask.
"""

from __future__ import annotations

import importlib
import os
import re
import sys
from pathlib import Path

from flask import render_template


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_app_for_environment(environment: str):
    os.environ["ENVIRONMENT"] = environment

    if "app" in sys.modules:
        del sys.modules["app"]

    app_module = importlib.import_module("app")
    return importlib.reload(app_module)


def _assert_contains(text: str, needle: str, context: str) -> None:
    if needle not in text:
        raise AssertionError(f"Missing expected token '{needle}' in {context}")


def _extract_input_value(html: str, input_id: str) -> str | None:
    match = re.search(
        rf'<input[^>]*id="{re.escape(input_id)}"[^>]*value="([^"]*)"',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return match.group(1) if match else None


def _run_mode_checks(environment: str) -> None:
    app_module = _load_app_for_environment(environment)
    flask_app = app_module.app

    with flask_app.test_client() as client:
        graph_response = client.get("/graph")
        if graph_response.status_code != 200:
            raise AssertionError(f"[{environment}] /graph returned {graph_response.status_code}")
        graph_html = graph_response.get_data(as_text=True)
        # v0.4: /graph is unified with / — check for the v0.4 layout config token
        _assert_contains(graph_html, "LEGACY_DASHBOARD_CONFIG", f"{environment} /graph")

        admin_response = client.get("/admin")
        if admin_response.status_code != 200:
            raise AssertionError(f"[{environment}] /admin returned {admin_response.status_code}")
        admin_html = admin_response.get_data(as_text=True)
        # v0.4: /admin is also unified with / — same config token
        _assert_contains(admin_html, "LEGACY_DASHBOARD_CONFIG", f"{environment} /admin")

    with flask_app.app_context():
        defaults = app_module._get_graph_template_defaults()
        legacy_html = render_template(
            "index.html",
            is_production=(environment == "production"),
            scenario_defaults=defaults,
        )

    _assert_contains(legacy_html, "LEGACY_DASHBOARD_CONFIG", f"{environment} index.html")
    _assert_contains(legacy_html, 'id="industry"', f"{environment} index.html")
    _assert_contains(legacy_html, 'id="industryOther"', f"{environment} index.html")

    company_value = _extract_input_value(legacy_html, "companyName")
    budget_value = _extract_input_value(legacy_html, "budget")

    if environment == "production":
        if company_value != "":
            raise AssertionError(
                f"[production] Expected blank companyName in legacy template, got: {company_value!r}"
            )
        if budget_value != "":
            raise AssertionError(
                f"[production] Expected blank budget in legacy template, got: {budget_value!r}"
            )
    else:
        if company_value != "Amazon Granite LLC":
            raise AssertionError(
                f"[development] Expected dev companyName default, got: {company_value!r}"
            )
        if budget_value not in {"1000", "1000.0"}:
            raise AssertionError(
                f"[development] Expected dev budget default 1000, got: {budget_value!r}"
            )

    print(f"✓ {environment:<11} /graph, /admin, legacy index template")


def main() -> int:
    original_environment = os.environ.get("ENVIRONMENT")
    try:
        for environment in ("development", "production"):
            _run_mode_checks(environment)
    finally:
        if original_environment is None:
            os.environ.pop("ENVIRONMENT", None)
        else:
            os.environ["ENVIRONMENT"] = original_environment

    print("\nSmoke check complete: all routes/templates rendered as expected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
