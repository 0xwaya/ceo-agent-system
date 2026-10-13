"""Offline coverage for Stripe fulfillment, ownership, and execution allowances."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import hashlib
import hmac
import json
import time
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import stripe

from services.billing_service import BillingService, BillingUnavailable, InsufficientCredits, units


@pytest.fixture
def billing(tmp_path, monkeypatch):
    service = BillingService(tmp_path / "billing.sqlite3")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_offline")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_offline")
    monkeypatch.setenv("BILLING_ENABLED", "true")
    monkeypatch.setenv("BILLING_PUBLIC_URL", "http://localhost:5001")
    monkeypatch.setenv("BILLING_ALLOW_LIVE", "false")
    monkeypatch.setattr("services.billing_service.billing_service", service)
    monkeypatch.setattr("services.billing_routes.billing_service", service)
    return service


def order(service, kind="membership"):
    with closing(service.connect()) as db, db:
        service._wallet(db, "owner")
        db.execute("UPDATE billing_wallets SET customer='cus_owner' WHERE workspace='owner'")
        db.execute(
            "INSERT INTO billing_orders(id,workspace,kind,amount,allowance,session) "
            "VALUES('order','owner',?,?,?,'cs_order')",
            (kind, 2900 if kind == "membership" else 500, 1000 if kind == "membership" else 500),
        )


def subscription():
    return {
        "id": "sub_owner",
        "customer": "cus_owner",
        "status": "active",
        "metadata": {"order_id": "order"},
        "cancel_at_period_end": False,
    }


def invoice(identifier="in_paid", start=None):
    start = start or int(time.time()) - 60
    return {
        "id": identifier,
        "subscription": "sub_owner",
        "customer": "cus_owner",
        "status": "paid",
        "currency": "usd",
        "amount_paid": 2900,
        "billing_reason": "subscription_cycle",
        "lines": {"data": [{"amount": 2900, "period": {"start": start, "end": start + 2592000}}]},
    }


def event(obj, kind="invoice.paid", identifier="evt_paid"):
    return {"id": identifier, "type": kind, "livemode": False, "data": {"object": obj}}


def mock_stripe(service, monkeypatch):
    client = MagicMock()
    client.v1.subscriptions.retrieve.return_value = subscription()
    monkeypatch.setattr(service, "stripe", lambda: client)
    return client


def test_balance_and_atomic_reservations(billing):
    billing.credit_balance("owner", 10, reference_id="deposit")
    billing.credit_balance("owner", 10, reference_id="deposit")
    assert billing.get_balance("owner")["balance_usd"] == 10
    billing.reserve("owner", "run", 3)
    assert billing.get_balance("owner")["balance_usd"] == 7
    billing.settle("run", 1)
    assert billing.get_balance("owner")["balance_usd"] == 9
    with pytest.raises(ValueError):
        billing.settle("run", 1)
    with pytest.raises(InsufficientCredits):
        billing.reserve("owner", "over", 10)


def test_concurrent_spend_does_not_overdraw(billing):
    billing.credit_balance("owner", 1)

    def spend(index):
        try:
            billing.reserve("owner", str(index), 0.75)
            return True
        except InsufficientCredits:
            return False

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sum(executor.map(spend, range(2))) == 1
    assert billing.get_balance("owner")["balance_usd"] == 0.25


@pytest.mark.parametrize("amount", ["NaN", "Infinity", "-1"])
def test_invalid_money_rejected(amount):
    with pytest.raises(ValueError):
        units(amount)


def test_quote_is_not_business_budget(billing):
    quote = billing.calculate_task_quote(
        {"task_id": "task", "estimated_budget": 10000, "estimated_days": 10}, "researcher"
    )
    assert quote["scenario_budget_reference"] == 10000
    assert quote["estimate_only"]
    assert quote["breakdown"]["tool_cost_usd"] == 0
    assert 0 < quote["total_quoted_usd"] < 1


def test_invoice_deduplication_and_monthly_reset(billing, monkeypatch):
    order(billing)
    mock_stripe(billing, monkeypatch)
    paid = invoice()
    billing.handle_event(event(paid))
    billing.handle_event(event(paid))
    billing.handle_event(event(paid, identifier="evt_another_delivery"))
    assert billing.get_balance("owner")["included_usd"] == 10
    billing.credit_balance("owner", 5)
    billing.reserve("owner", "run", 4)
    billing.settle("run", 4)
    assert billing.get_balance("owner")["balance_usd"] == 11
    billing.handle_event(
        event(
            invoice("in_next", paid["lines"]["data"][0]["period"]["start"] + 100),
            identifier="evt_next",
        )
    )
    assert billing.get_balance("owner")["balance_usd"] == 15
    billing.handle_event(event(paid, identifier="evt_late"))
    assert billing.get_balance("owner")["balance_usd"] == 15


@pytest.mark.parametrize(
    "field,value",
    [
        ("amount_paid", 0),
        ("currency", "eur"),
        ("customer", "cus_other"),
        ("status", "open"),
        ("paid_out_of_band", True),
    ],
)
def test_invoice_mismatch_does_not_grant(billing, monkeypatch, field, value):
    order(billing)
    mock_stripe(billing, monkeypatch)
    paid = invoice()
    paid[field] = value
    with pytest.raises(ValueError):
        billing.handle_event(event(paid))
    assert billing.get_balance("owner")["balance_usd"] == 0
    with closing(billing.connect()) as db:
        assert db.execute("SELECT COUNT(*) FROM billing_events").fetchone()[0] == 0


def test_modern_invoice_parent_and_proration(billing, monkeypatch):
    order(billing)
    mock_stripe(billing, monkeypatch)
    paid = invoice()
    paid.pop("subscription")
    paid["parent"] = {"subscription_details": {"subscription": "sub_owner"}}
    paid["billing_reason"] = "subscription_update"
    billing.handle_event(event(paid))
    assert billing.get_balance("owner")["balance_usd"] == 0
    paid["billing_reason"] = "subscription_cycle"
    billing.handle_event(event(paid, identifier="evt_cycle"))
    assert billing.get_balance("owner")["balance_usd"] == 10


def test_expiry_and_cross_period_reservation(billing, monkeypatch):
    order(billing)
    mock_stripe(billing, monkeypatch)
    paid = invoice()
    billing.handle_event(event(paid))
    billing.reserve("owner", "run", 3)
    billing.handle_event(event(invoice("in_next", int(time.time()) - 10), identifier="evt_next"))
    billing.settle("run", 1)
    assert billing.get_balance("owner")["included_usd"] == 10
    billing.credit_balance("owner", 5)
    with closing(billing.connect()) as db, db:
        db.execute("UPDATE billing_wallets SET expires=1")
    assert billing.get_balance("owner")["balance_usd"] == 5


def test_topup_verified_and_deduplicated(billing):
    order(billing, "topup")
    checkout = {
        "id": "cs_order",
        "customer": "cus_owner",
        "metadata": {"order_id": "order"},
        "payment_status": "unpaid",
        "currency": "usd",
        "amount_total": 500,
    }
    billing.handle_event(event(checkout, "checkout.session.completed"))
    assert billing.get_balance("owner")["balance_usd"] == 0
    checkout["payment_status"] = "paid"
    billing.handle_event(event(checkout, "checkout.session.completed", "evt_paid_checkout"))
    billing.handle_event(event(checkout, "checkout.session.completed", "evt_duplicate_checkout"))
    assert billing.get_balance("owner")["topup_usd"] == 5


def test_cancel_and_refund_stop_usage(billing, monkeypatch):
    order(billing)
    client = mock_stripe(billing, monkeypatch)
    billing.handle_event(event(invoice()))
    cancelled = subscription()
    cancelled["status"] = "canceled"
    client.v1.subscriptions.retrieve.return_value = cancelled
    billing.handle_event(event(cancelled, "customer.subscription.deleted", "evt_cancel"))
    assert billing.get_balance("owner")["included_usd"] == 0
    billing.credit_balance("owner", 5)
    charge = {"id": "ch_refund", "customer": "cus_owner", "amount_refunded": 100}
    client.v1.charges.retrieve.return_value = charge
    billing.handle_event(event(charge, "charge.refunded", "evt_refund"))
    assert billing.get_balance("owner")["status"] == "review_required"
    with pytest.raises(InsufficientCredits):
        billing.reserve("owner", "refund_run", 0.1)


def test_checkout_is_hosted_subscription_with_server_price(billing, monkeypatch):
    client = mock_stripe(billing, monkeypatch)
    client.v1.customers.create.return_value = SimpleNamespace(id="cus_owner")
    client.v1.checkout.sessions.create.return_value = SimpleNamespace(
        id="cs_order", url="https://checkout.stripe.com/test"
    )
    billing.create_checkout("owner", "membership", 1)
    params = client.v1.checkout.sessions.create.call_args.args[0]
    assert params["mode"] == "subscription"
    assert params["payment_method_types"] == ["card"]
    assert params["line_items"][0]["price_data"]["unit_amount"] == 2900
    assert params["line_items"][0]["price_data"]["recurring"] == {"interval": "month"}
    assert billing.get_balance("owner")["balance_usd"] == 0
    client.v1.checkout.sessions.retrieve.return_value = SimpleNamespace(
        status="open", id="cs_order", url="https://checkout.stripe.com/test"
    )
    billing.create_checkout("owner", "membership")
    assert client.v1.checkout.sessions.create.call_count == 1


def test_stripe_errors_never_fall_back(billing, monkeypatch):
    client = mock_stripe(billing, monkeypatch)
    client.v1.customers.create.side_effect = stripe.APIConnectionError("offline")
    with pytest.raises(stripe.APIConnectionError):
        billing.create_checkout("owner", "membership")
    assert billing.get_balance("owner")["balance_usd"] == 0


def test_live_is_gated_and_origin_is_validated(billing, monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_offline")
    with pytest.raises(BillingUnavailable):
        billing.settings()
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_offline")
    monkeypatch.setenv("BILLING_PUBLIC_URL", "http://untrusted.example")
    with pytest.raises(BillingUnavailable):
        billing.settings()


def signed_payload(obj):
    raw = json.dumps(obj).encode()
    stamp = str(int(time.time()))
    signature = hmac.new(b"whsec_offline", stamp.encode() + b"." + raw, hashlib.sha256).hexdigest()
    return raw, f"t={stamp},v1={signature}"


def test_webhook_signature_and_no_browser_auth(billing, test_client, monkeypatch):
    import app

    monkeypatch.setitem(app.app.config, "ACCOUNT_AUTH_ENABLED", True)
    raw, signature = signed_payload(event({}, "unknown.event"))
    response = test_client.post(
        "/api/billing/webhook",
        data=raw,
        content_type="application/json",
        headers={"Stripe-Signature": signature},
    )
    assert response.status_code == 200
    response = test_client.post(
        "/api/billing/webhook",
        data=raw + b" ",
        content_type="application/json",
        headers={"Stripe-Signature": signature},
    )
    assert response.status_code == 400
    assert test_client.get("/api/billing/balance").status_code == 401
    assert test_client.get("/api/billing/mock-checkout?amount=1000").status_code != 200


def test_checkout_rejects_different_browser_hostname(billing, test_client):
    response = test_client.post(
        "/api/billing/checkout",
        json={"kind": "membership"},
        base_url="http://127.0.0.1:5001",
    )
    assert response.status_code == 503
    assert "http://localhost:5001" in response.json["error"]


def test_review_reconciliation_is_explicit(billing, monkeypatch):
    order(billing)
    client = mock_stripe(billing, monkeypatch)
    billing.credit_balance("owner", 5)
    charge = {"id": "ch_refund", "customer": "cus_owner", "amount_refunded": 500}
    client.v1.charges.retrieve.return_value = charge
    billing.handle_event(event(charge, "charge.refunded", "evt_refund"))
    billing.reconcile("owner", 0)
    assert billing.get_balance("owner")["balance_usd"] == 0
    assert billing.get_balance("owner")["status"] == "reconciled"
    with pytest.raises(ValueError):
        billing.reconcile("owner", 5)


def test_usage_callback_blocks_before_provider_call(billing, tmp_path):
    from services.job_service import JobStore
    from services.usage_service import UsageCallback
    from langchain_core.messages import HumanMessage

    store = JobStore(tmp_path / "jobs.sqlite3")
    job = store.begin_operation("owner")
    callback = UsageCallback(store, job)
    # conftest controls model pricing in other tests; configure explicitly here.
    from unittest.mock import patch
    from config import OPENAI_MODEL

    with patch.dict(
        "os.environ",
        {
            "PRICED_MODEL": OPENAI_MODEL,
            "MODEL_INPUT_USD_PER_MILLION": "1",
            "MODEL_OUTPUT_USD_PER_MILLION": "2",
        },
    ):
        with pytest.raises(InsufficientCredits):
            callback.on_chat_model_start(
                {},
                [[HumanMessage(content="hello")]],
                run_id="run",
                invocation_params={"max_tokens": 100},
            )
        billing.credit_balance("owner", 1)
        callback.on_chat_model_start(
            {},
            [[HumanMessage(content="hello")]],
            run_id="run",
            invocation_params={"max_tokens": 100},
        )
        callback.on_llm_end(
            SimpleNamespace(
                llm_output={"token_usage": {"prompt_tokens": 10, "completion_tokens": 5}}
            ),
            run_id="run",
        )
    assert billing.get_balance("owner")["balance_usd"] == 0.99998
