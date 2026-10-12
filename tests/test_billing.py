"""Tests for Billing & Stripe integration architecture."""

from services.billing_service import BillingService


def test_billing_service_initialization(tmp_path):
    db_file = tmp_path / "test_billing.db"
    billing = BillingService(db_path=db_file)

    balance = billing.get_balance("ws_test_1")
    assert balance["balance_usd"] == 0.0
    assert balance["currency"] == "usd"


def test_credit_and_deduct_lifecycle(tmp_path):
    db_file = tmp_path / "test_billing.db"
    billing = BillingService(db_path=db_file)

    # Add credits
    credit_res = billing.credit_balance("ws_test_1", 10.0, description="Test deposit")
    assert credit_res["success"] is True
    assert credit_res["balance_usd"] == 10.0

    # Verify updated balance
    assert billing.get_balance("ws_test_1")["balance_usd"] == 10.0

    # Deduct credits for task execution
    deducted = billing.deduct_credits("ws_test_1", 2.50, task_id="task_101", description="SEO Task")
    assert deducted is True
    assert billing.get_balance("ws_test_1")["balance_usd"] == 7.50

    # Attempt to deduct more than remaining
    insufficient = billing.deduct_credits("ws_test_1", 20.0, task_id="task_102")
    assert insufficient is False
    assert billing.get_balance("ws_test_1")["balance_usd"] == 7.50


def test_calculate_task_quote():
    billing = BillingService()
    sample_task = {
        "task_id": "task_0",
        "task_name": "Market Research",
        "estimated_budget": 200.0,
        "estimated_days": 10,
    }
    quote = billing.calculate_task_quote(sample_task, "researcher")
    assert quote["task_id"] == "task_0"
    assert quote["agent_type"] == "researcher"
    assert quote["total_quoted_usd"] > 0
    assert "estimated_tokens" in quote["breakdown"]
    assert "tool_cost_usd" in quote["breakdown"]
    assert "platform_fee_usd" in quote["breakdown"]


def test_stripe_checkout_session_mock():
    billing = BillingService()
    checkout = billing.create_stripe_checkout_session(
        workspace_id="ws_user_42",
        amount_usd=5.0,
        task_id="task_0",
    )
    assert checkout["mode"] == "sandbox"
    assert checkout["amount_usd"] == 5.0
    assert "mock-checkout" in checkout["checkout_url"]
