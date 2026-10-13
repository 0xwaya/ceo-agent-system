"""Validate sandbox credentials and hosted Checkout without charging a card."""

import argparse
from contextlib import closing
from pathlib import Path
import sys
import tempfile
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services import environment_service  # noqa: E402,F401
from services.billing_service import BillingService  # noqa: E402
import stripe  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", action="store_true", help="Create and expire a test Checkout")
    parser.add_argument("--setup-portal", action="store_true", help="Configure the sandbox portal")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="wayalabs-stripe-") as directory:
        service = BillingService(Path(directory) / "billing.sqlite3")
        settings = service.settings()
        if settings["live"]:
            raise RuntimeError("This verification tool refuses live credentials")
        client = service.stripe()
        if client.v1.balance.retrieve().livemode:
            raise RuntimeError("Expected sandbox account")
        print("Sandbox authentication verified (no credentials displayed).")
        configs = client.v1.billing_portal.configurations.list({"limit": 100}).data
        owned = [
            item
            for item in configs
            if item.active and item.metadata.get("application") == "ceo-agent-system"
        ]
        if args.setup_portal and not owned:
            client.v1.billing_portal.configurations.create(
                {
                    "business_profile": {"headline": "Manage your WayaLabs AI membership"},
                    "features": {
                        "invoice_history": {"enabled": True},
                        "payment_method_update": {"enabled": True},
                        "subscription_cancel": {"enabled": True, "mode": "at_period_end"},
                    },
                    "metadata": {"application": "ceo-agent-system"},
                },
                options={"idempotency_key": "ceo-agent-system:portal:v1"},
            )
            print(
                "Sandbox portal configured: invoices, payment methods, end-of-period cancellation."
            )
        elif owned:
            print("Sandbox membership portal configuration verified.")
        else:
            print("Portal needs setup: rerun with --setup-portal.")
        if args.checkout:
            workspace = "integration-check-" + uuid.uuid4().hex
            checkout = None
            try:
                checkout = service.create_checkout(workspace, "membership")
                session = client.v1.checkout.sessions.retrieve(checkout["session_id"])
                assert session.mode == "subscription" and not session.livemode
                assert session.amount_total == settings["price"]
                assert session.url.startswith("https://checkout.stripe.com/")
                print("Hosted sandbox subscription Checkout verified; no payment submitted.")
                portal_url = service.create_portal(workspace)
                assert portal_url.startswith("https://billing.stripe.com/")
                print("Sandbox customer portal session verified.")
            finally:
                if checkout:
                    client.v1.checkout.sessions.expire(checkout["session_id"])
                with closing(service.connect()) as db:
                    row = db.execute(
                        "SELECT customer FROM billing_wallets WHERE workspace=?", (workspace,)
                    ).fetchone()
                if row and row["customer"]:
                    client.v1.customers.delete(row["customer"])
                print("Verification Checkout expired and its test customer removed.")


if __name__ == "__main__":
    try:
        main()
    except stripe.StripeError as exc:
        print(f"Stripe verification failed: {type(exc).__name__}", file=sys.stderr)
        sys.exit(1)
