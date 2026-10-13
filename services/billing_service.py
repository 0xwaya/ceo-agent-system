"""Stripe memberships and a transactional, fixed-precision execution allowance."""

from contextlib import closing
from decimal import Decimal, ROUND_CEILING
import os
from pathlib import Path
import sqlite3
import time
from urllib.parse import urlsplit
import uuid


class BillingUnavailable(RuntimeError):
    pass


class InsufficientCredits(RuntimeError):
    pass


def units(amount):
    value = Decimal(str(amount))
    if not value.is_finite() or value < 0:
        raise ValueError("Amount must be finite and non-negative")
    return int((value * 1_000_000).to_integral_value(rounding=ROUND_CEILING))


class BillingService:
    def __init__(self, db_path=None):
        key = os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_API_KEY", "")
        filename = (
            "billing-live.db" if key.startswith(("sk_live_", "rk_live_")) else "billing-sandbox.db"
        )
        self.db_path = Path(db_path or Path(__file__).resolve().parents[1] / "data" / filename)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as db, db:
            db.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS billing_wallets(
                    workspace TEXT PRIMARY KEY, included INTEGER NOT NULL DEFAULT 0,
                    topup INTEGER NOT NULL DEFAULT 0, expires INTEGER NOT NULL DEFAULT 0,
                    customer TEXT UNIQUE, subscription TEXT UNIQUE, status TEXT DEFAULT 'none',
                    cancel_at_period_end INTEGER NOT NULL DEFAULT 0,
                    latest_period INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS billing_orders(
                    id TEXT PRIMARY KEY, workspace TEXT NOT NULL, kind TEXT NOT NULL,
                    amount INTEGER NOT NULL, allowance INTEGER NOT NULL,
                    session TEXT UNIQUE, status TEXT NOT NULL DEFAULT 'pending');
                CREATE UNIQUE INDEX IF NOT EXISTS pending_membership
                    ON billing_orders(workspace) WHERE kind='membership' AND status='pending';
                CREATE TABLE IF NOT EXISTS billing_events(id TEXT PRIMARY KEY);
                CREATE TABLE IF NOT EXISTS billing_grants(
                    reference TEXT PRIMARY KEY, workspace TEXT NOT NULL, kind TEXT NOT NULL,
                    amount INTEGER NOT NULL, period INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS billing_reservations(
                    id TEXT PRIMARY KEY, workspace TEXT NOT NULL, included INTEGER NOT NULL,
                    topup INTEGER NOT NULL, period INTEGER NOT NULL, status TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS billing_audit(
                    id INTEGER PRIMARY KEY, workspace TEXT NOT NULL, amount INTEGER NOT NULL,
                    kind TEXT NOT NULL, reference TEXT NOT NULL, created INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS billing_reversals(
                    charge TEXT PRIMARY KEY, refunded INTEGER NOT NULL DEFAULT 0,
                    disputed INTEGER NOT NULL DEFAULT 0);
                """
            )
        self.db_path.chmod(0o600)

    def connect(self):
        db = sqlite3.connect(self.db_path, timeout=30)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def enabled():
        default = (
            "true" if os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_API_KEY") else "false"
        )
        return os.getenv("BILLING_ENABLED", default).lower() == "true"

    @staticmethod
    def settings():
        key = os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_API_KEY", "")
        live = key.startswith(("sk_live_", "rk_live_"))
        if not key.startswith(("sk_test_", "rk_test_", "sk_live_", "rk_live_")):
            raise BillingUnavailable("Configure a valid Stripe secret key")
        if live and os.getenv("BILLING_ALLOW_LIVE", "false").lower() != "true":
            raise BillingUnavailable("Live payments are disabled; use the WayaLabs sandbox")
        origin = os.getenv("BILLING_PUBLIC_URL", "http://localhost:5001").rstrip("/")
        parsed = urlsplit(origin)
        local = parsed.hostname in {"localhost", "127.0.0.1"}
        if (
            not parsed.netloc
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path
            or (parsed.scheme != "https" and not (parsed.scheme == "http" and local and not live))
        ):
            raise BillingUnavailable("BILLING_PUBLIC_URL must be a trusted HTTPS origin")
        price = int(os.getenv("STRIPE_MEMBERSHIP_AMOUNT_CENTS", "2900"))
        allowance = int(os.getenv("STRIPE_MEMBERSHIP_CREDITS_CENTS", "1000"))
        if price < 50 or allowance <= 0 or allowance > price:
            raise BillingUnavailable("Membership price/allowance configuration is invalid")
        return {
            "key": key,
            "live": live,
            "origin": origin,
            "price": price,
            "allowance": allowance,
        }

    def stripe(self):
        import stripe

        return stripe.StripeClient(self.settings()["key"])

    def _wallet(self, db, workspace):
        db.execute("INSERT OR IGNORE INTO billing_wallets(workspace) VALUES(?)", (workspace,))
        db.execute(
            "UPDATE billing_wallets SET included=0 WHERE workspace=? AND expires<=?",
            (workspace, int(time.time())),
        )
        return db.execute(
            "SELECT * FROM billing_wallets WHERE workspace=?", (workspace,)
        ).fetchone()

    def get_balance(self, workspace_id):
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = self._wallet(db, workspace_id)
            history = [
                dict(item)
                for item in db.execute(
                    "SELECT amount,kind,reference,created FROM billing_audit "
                    "WHERE workspace=? ORDER BY id DESC LIMIT 20",
                    (workspace_id,),
                )
            ]
        return {
            "workspace_id": workspace_id,
            "balance_usd": (row["included"] + row["topup"]) / 1_000_000,
            "included_usd": row["included"] / 1_000_000,
            "topup_usd": row["topup"] / 1_000_000,
            "currency": "usd",
            "status": row["status"],
            "has_subscription": bool(row["subscription"]),
            "cancel_at_period_end": bool(row["cancel_at_period_end"]),
            "period_end": row["expires"],
            "billing_enabled": self.enabled(),
            "history": history,
        }

    def _audit(self, db, workspace, amount, kind, reference):
        db.execute(
            "INSERT INTO billing_audit(workspace,amount,kind,reference,created) VALUES(?,?,?,?,?)",
            (workspace, amount, kind, reference, int(time.time())),
        )

    def credit_balance(
        self, workspace_id, amount_usd, kind="topup", reference_id=None, description=""
    ):
        amount = units(amount_usd)
        if not amount:
            raise ValueError("Credit amount must be greater than zero")
        reference = reference_id or uuid.uuid4().hex
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            self._wallet(db, workspace_id)
            changed = db.execute(
                "INSERT OR IGNORE INTO billing_grants(reference,workspace,kind,amount) "
                "VALUES(?,?,?,?)",
                (reference, workspace_id, kind, amount),
            ).rowcount
            if changed:
                db.execute(
                    "UPDATE billing_wallets SET topup=topup+? WHERE workspace=?",
                    (amount, workspace_id),
                )
                self._audit(db, workspace_id, amount, kind, reference)
        return {"success": True, **self.get_balance(workspace_id)}

    def reserve(self, workspace, reference, amount_usd):
        amount = units(amount_usd)
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM billing_reservations WHERE id=?", (reference,)).fetchone():
                raise ValueError("Execution reservation already exists")
            row = self._wallet(db, workspace)
            if row["status"] == "review_required":
                raise InsufficientCredits("Billing is paused pending refund/dispute reconciliation")
            if row["included"] + row["topup"] < amount:
                raise InsufficientCredits(
                    "Execution allowance exhausted. Upgrade, top up, or wait for renewal."
                )
            included = min(row["included"], amount)
            topup = amount - included
            db.execute(
                "UPDATE billing_wallets SET included=included-?,topup=topup-? WHERE workspace=?",
                (included, topup, workspace),
            )
            db.execute(
                "INSERT INTO billing_reservations VALUES(?,?,?,?,?,'reserved')",
                (reference, workspace, included, topup, row["latest_period"]),
            )

    def settle(self, reference, actual_usd):
        actual = units(actual_usd)
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM billing_reservations WHERE id=?", (reference,)
            ).fetchone()
            if row is None or row["status"] != "reserved":
                raise ValueError("Execution reservation is not open")
            reserved = row["included"] + row["topup"]
            # Never hide a provider overrun; charge the reservation and stop execution.
            used = min(actual, reserved)
            included_used = min(used, row["included"])
            topup_used = used - included_used
            wallet = self._wallet(db, row["workspace"])
            restore = (
                row["included"] - included_used
                if wallet["latest_period"] == row["period"] and wallet["expires"] > time.time()
                else 0
            )
            db.execute(
                "UPDATE billing_wallets SET included=included+?,topup=topup+? WHERE workspace=?",
                (restore, row["topup"] - topup_used, row["workspace"]),
            )
            db.execute("UPDATE billing_reservations SET status='settled' WHERE id=?", (reference,))
            self._audit(db, row["workspace"], -used, "execution", reference)
        if actual > reserved:
            raise RuntimeError("Provider exceeded the approved execution reservation")

    def deduct_credits(self, workspace_id, amount_usd, task_id, description=""):
        reference = uuid.uuid4().hex
        try:
            self.reserve(workspace_id, reference, amount_usd)
        except InsufficientCredits:
            return False
        self.settle(reference, amount_usd)
        return True

    def calculate_task_quote(self, task, agent_type):
        if not isinstance(task, dict) or not isinstance(agent_type, str):
            raise ValueError("Task must be an object and agent_type must be text")
        # Estimates are display-only. Actual provider usage is enforced by UsageCallback.
        days = max(1, min(365, int(task.get("estimated_days") or task.get("timeline_days") or 1)))
        tokens = 30000 + days * 2000
        compute = round(tokens * 0.0000006, 4)
        return {
            "task_id": task.get("task_id", "task"),
            "agent_type": agent_type,
            "total_quoted_usd": round(compute, 2),
            "estimate_only": True,
            "scenario_budget_reference": task.get("estimated_budget", task.get("budget", 0)),
            "breakdown": {
                "estimated_tokens": tokens,
                "token_cost_usd": compute,
                "tool_service": "External purchases require separate approval",
                "tool_cost_usd": 0,
                "platform_fee_usd": 0,
            },
        }

    def create_checkout(self, workspace, kind, amount_cents=None):
        settings = self.settings()
        if kind not in {"membership", "topup"}:
            raise ValueError("Select membership or topup")
        amount = settings["price"] if kind == "membership" else amount_cents
        if type(amount) is not int or amount not in (
            {500, 1500, 2500} if kind == "topup" else {amount}
        ):
            raise ValueError("Select a supported top-up amount")
        identifier = uuid.uuid4().hex
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            wallet = self._wallet(db, workspace)
            if wallet["status"] == "review_required":
                raise ValueError("Resolve the refund/dispute before purchasing more credits")
            if kind == "membership" and wallet["subscription"]:
                raise ValueError("Manage the existing membership in the customer portal")
            existing = db.execute(
                "SELECT * FROM billing_orders WHERE workspace=? AND kind='membership' "
                "AND status='pending'",
                (workspace,),
            ).fetchone()
            if kind == "membership" and existing:
                identifier = existing["id"]
                amount = existing["amount"]
            else:
                db.execute(
                    "INSERT INTO billing_orders(id,workspace,kind,amount,allowance) "
                    "VALUES(?,?,?,?,?)",
                    (
                        identifier,
                        workspace,
                        kind,
                        amount,
                        settings["allowance"] if kind == "membership" else amount,
                    ),
                )
        client = self.stripe()
        if not wallet["customer"]:
            customer = client.v1.customers.create(
                {"metadata": {"workspace_id": workspace}},
                options={"idempotency_key": f"customer:{workspace}"},
            )
            with closing(self.connect()) as db, db:
                db.execute(
                    "UPDATE billing_wallets SET customer=? WHERE workspace=?",
                    (customer.id, workspace),
                )
            customer_id = customer.id
        else:
            customer_id = wallet["customer"]
        if kind == "membership" and existing and existing["session"]:
            previous = client.v1.checkout.sessions.retrieve(existing["session"])
            if previous.status == "open":
                return {"checkout_url": previous.url, "session_id": previous.id}
            if previous.status == "complete":
                raise ValueError("Payment is processing; wait for verified webhook confirmation")
            with closing(self.connect()) as db, db:
                db.execute("UPDATE billing_orders SET status='expired' WHERE id=?", (identifier,))
            return self.create_checkout(workspace, kind)
        metadata = {"order_id": identifier, "workspace_id": workspace}
        price_data = {
            "currency": "usd",
            "unit_amount": amount,
            "product_data": {
                "name": "WayaLabs AI Membership" if kind == "membership" else "AI execution top-up"
            },
        }
        params = {
            "mode": "subscription" if kind == "membership" else "payment",
            "customer": customer_id,
            "payment_method_types": ["card"],
            "line_items": [{"price_data": price_data, "quantity": 1}],
            "metadata": metadata,
            "client_reference_id": workspace,
            "success_url": settings["origin"] + "/?payment=processing",
            "cancel_url": settings["origin"] + "/?payment=cancelled",
        }
        if kind == "membership":
            price_data["recurring"] = {"interval": "month"}
            params["subscription_data"] = {"metadata": metadata}
        else:
            params["payment_intent_data"] = {"metadata": metadata}
        checkout = client.v1.checkout.sessions.create(
            params, options={"idempotency_key": f"checkout:{identifier}"}
        )
        with closing(self.connect()) as db, db:
            db.execute("UPDATE billing_orders SET session=? WHERE id=?", (checkout.id, identifier))
        return {"checkout_url": checkout.url, "session_id": checkout.id}

    def create_portal(self, workspace):
        settings = self.settings()
        with closing(self.connect()) as db:
            row = db.execute(
                "SELECT customer FROM billing_wallets WHERE workspace=?", (workspace,)
            ).fetchone()
        if not row or not row["customer"]:
            raise ValueError("Start a membership before opening subscription management")
        client = self.stripe()
        configurations = client.v1.billing_portal.configurations.list({"limit": 100}).data
        owned = [
            item
            for item in configurations
            if item.active and item.metadata.get("application") == "ceo-agent-system"
        ]
        if not owned:
            raise BillingUnavailable("Configure the WayaLabs customer portal before using it")
        portal = client.v1.billing_portal.sessions.create(
            {
                "customer": row["customer"],
                "configuration": owned[0].id,
                "return_url": settings["origin"] + "/",
            }
        )
        return portal.url

    def verify_event(self, payload, signature):
        import stripe

        secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        if not secret.startswith("whsec_"):
            raise BillingUnavailable("Configure STRIPE_WEBHOOK_SECRET for this webhook endpoint")
        event = stripe.Webhook.construct_event(payload, signature, secret)
        if bool(event["livemode"]) != self.settings()["live"]:
            raise ValueError("Webhook mode does not match the configured Stripe account")
        return event

    def handle_event(self, event):
        event_type = event["type"]
        obj = event["data"]["object"]
        subscription = None
        if event_type == "invoice.paid":
            subscription_id = obj.get("subscription") or (
                (obj.get("parent") or {}).get("subscription_details") or {}
            ).get("subscription")
            if not subscription_id:
                return
            subscription = self.stripe().v1.subscriptions.retrieve(subscription_id)
        elif event_type in {
            "customer.subscription.updated",
            "customer.subscription.deleted",
            "invoice.payment_failed",
        }:
            subscription_id = (
                obj.get("id")
                if event_type.startswith("customer.")
                else (
                    obj.get("subscription")
                    or ((obj.get("parent") or {}).get("subscription_details") or {}).get(
                        "subscription"
                    )
                )
            )
            if not subscription_id:
                return
            subscription = self.stripe().v1.subscriptions.retrieve(subscription_id)
        elif event_type in {"charge.refunded", "charge.dispute.created"}:
            charge_id = obj["id"] if event_type == "charge.refunded" else obj["charge"]
            charge = self.stripe().v1.charges.retrieve(charge_id)
            obj = charge
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            if not db.execute(
                "INSERT OR IGNORE INTO billing_events VALUES(?)", (event["id"],)
            ).rowcount:
                return
            if event_type in {"charge.refunded", "charge.dispute.created"}:
                self._reverse(db, obj, event_type)
            elif subscription is not None:
                metadata = subscription.get("metadata") or {}
                order = db.execute(
                    "SELECT * FROM billing_orders WHERE id=? AND kind='membership'",
                    (metadata.get("order_id"),),
                ).fetchone()
                if not order:
                    return  # Not a subscription created by this application.
                wallet = self._wallet(db, order["workspace"])
                if wallet["status"] == "review_required":
                    raise ValueError("Refund/dispute requires reconciliation before further grants")
                if subscription["customer"] != wallet["customer"]:
                    raise ValueError("Subscription customer does not match its workspace")
                if wallet["subscription"] and wallet["subscription"] != subscription["id"]:
                    raise ValueError("A different membership is already linked")
                db.execute(
                    "UPDATE billing_wallets SET subscription=?,status=?,cancel_at_period_end=? "
                    "WHERE workspace=?",
                    (
                        subscription["id"],
                        subscription["status"],
                        int(subscription.get("cancel_at_period_end", False)),
                        order["workspace"],
                    ),
                )
                if subscription["status"] in {"canceled", "unpaid", "incomplete_expired"}:
                    db.execute(
                        "UPDATE billing_wallets SET included=0 WHERE workspace=?",
                        (order["workspace"],),
                    )
                    if subscription["status"] in {"canceled", "incomplete_expired"}:
                        db.execute(
                            "UPDATE billing_wallets SET subscription=NULL WHERE workspace=?",
                            (order["workspace"],),
                        )
                        db.execute(
                            "UPDATE billing_orders SET status='cancelled' WHERE id=?",
                            (order["id"],),
                        )
                if event_type == "invoice.paid":
                    self._invoice(db, obj, subscription, order)
            elif event_type == "checkout.session.completed":
                order = db.execute(
                    "SELECT * FROM billing_orders WHERE id=?",
                    ((obj.get("metadata") or {}).get("order_id"),),
                ).fetchone()
                if not order:
                    return
                wallet = self._wallet(db, order["workspace"])
                if obj["customer"] != wallet["customer"] or obj["id"] != order["session"]:
                    raise ValueError("Checkout does not match its order")
                if order["kind"] == "topup" and obj.get("payment_status") == "paid":
                    if obj["currency"] != "usd" or obj["amount_total"] != order["amount"]:
                        raise ValueError("Checkout amount or currency mismatch")
                    if db.execute(
                        "INSERT OR IGNORE INTO billing_grants VALUES(?,?,?,?,0)",
                        (obj["id"], order["workspace"], "topup", order["allowance"] * 10000),
                    ).rowcount:
                        db.execute(
                            "UPDATE billing_wallets SET topup=topup+? WHERE workspace=?",
                            (order["allowance"] * 10000, order["workspace"]),
                        )
                        self._audit(
                            db, order["workspace"], order["allowance"] * 10000, "topup", obj["id"]
                        )
                        db.execute(
                            "UPDATE billing_orders SET status='paid' WHERE id=?", (order["id"],)
                        )

    def _invoice(self, db, invoice, subscription, order):
        if invoice.get("billing_reason") not in {"subscription_create", "subscription_cycle"}:
            return  # Prorations/plan changes must not create another monthly allowance.
        if (
            invoice.get("status") != "paid"
            or invoice.get("paid_out_of_band")
            or invoice.get("currency") != "usd"
            or invoice.get("amount_paid") != order["amount"]
            or invoice.get("customer") != subscription["customer"]
        ):
            raise ValueError("Invoice payment, customer, amount or currency mismatch")
        lines = (invoice.get("lines") or {}).get("data") or []
        if len(lines) != 1 or lines[0].get("amount") != order["amount"]:
            raise ValueError("Expected one full monthly membership invoice line")
        period = lines[0]["period"]
        if period["end"] <= period["start"]:
            raise ValueError("Invalid invoice period")
        workspace = order["workspace"]
        amount = order["allowance"] * 10000
        if not db.execute(
            "INSERT OR IGNORE INTO billing_grants VALUES(?,?,?,?,?)",
            (invoice["id"], workspace, "membership", amount, period["start"]),
        ).rowcount:
            return
        wallet = self._wallet(db, workspace)
        if (
            period["start"] > wallet["latest_period"]
            and period["end"] > time.time()
            and subscription["status"] in {"active", "past_due"}
        ):
            db.execute(
                "UPDATE billing_wallets SET included=?,expires=?,latest_period=? WHERE workspace=?",
                (amount, period["end"], period["start"], workspace),
            )
            self._audit(db, workspace, amount, "membership", invoice["id"])
        db.execute("UPDATE billing_orders SET status='paid' WHERE id=?", (order["id"],))

    def _reverse(self, db, charge, event_type):
        wallet = db.execute(
            "SELECT * FROM billing_wallets WHERE customer=?", (charge.get("customer"),)
        ).fetchone()
        if not wallet:
            return
        old = db.execute(
            "SELECT * FROM billing_reversals WHERE charge=?", (charge["id"],)
        ).fetchone()
        refunded = charge.get("amount_refunded", 0)
        disputed = int(event_type == "charge.dispute.created")
        if old and refunded <= old["refunded"] and disputed <= old["disputed"]:
            return
        db.execute(
            "INSERT INTO billing_reversals VALUES(?,?,?) ON CONFLICT(charge) DO UPDATE SET "
            "refunded=MAX(refunded,excluded.refunded),disputed=MAX(disputed,excluded.disputed)",
            (charge["id"], refunded, disputed),
        )
        # Used credits cannot be automatically recovered: freeze until operator reconciliation.
        db.execute(
            "UPDATE billing_wallets SET included=0,status='review_required' WHERE workspace=?",
            (wallet["workspace"],),
        )
        self._audit(db, wallet["workspace"], 0, "refund_dispute_review", charge["id"])

    def reconcile(self, workspace, corrected_topup_usd):
        corrected = units(corrected_topup_usd)
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            wallet = self._wallet(db, workspace)
            if wallet["status"] != "review_required":
                raise ValueError("Workspace is not awaiting billing reconciliation")
            db.execute(
                "UPDATE billing_wallets SET included=0,topup=?,status='reconciled' "
                "WHERE workspace=?",
                (corrected, workspace),
            )
            self._audit(
                db,
                workspace,
                corrected - wallet["topup"],
                "manual_reconciliation",
                uuid.uuid4().hex,
            )


billing_service = BillingService()
