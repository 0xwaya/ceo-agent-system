"""
Credit and payment solicitation service for production monetized agent execution.

This module models:
- Workspace/Account credit balances
- Real-time task cost calculation (model tokens, third-party API tool calls, platform fee)
- Budget release requests & Stripe Checkout / PaymentIntent generation
- Verification and fulfillment of payments to unlock live execution
"""

from __future__ import annotations

import logging
import os
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class BillingService:
    """Manages workspace credit balances, task quote generation, and Stripe payment intents."""

    def __init__(self, db_path: Optional[str | Path] = None):
        if db_path is None:
            from config import PROJECT_ROOT

            data_dir = PROJECT_ROOT / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "billing.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create billing and credit ledger tables if they don't exist."""
        with closing(self._get_connection()) as conn, conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;

                CREATE TABLE IF NOT EXISTS workspace_credits (
                    workspace_id TEXT PRIMARY KEY,
                    balance_usd REAL NOT NULL DEFAULT 0.0,
                    currency TEXT NOT NULL DEFAULT 'usd',
                    tier TEXT NOT NULL DEFAULT 'standard',
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS credit_transactions (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    amount_usd REAL NOT NULL,
                    balance_after REAL NOT NULL,
                    kind TEXT NOT NULL, -- 'topup', 'task_deduction', 'refund'
                    reference_id TEXT,  -- stripe_session_id or task_id
                    description TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS task_payment_requests (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    agent_type TEXT NOT NULL,
                    quoted_amount_usd REAL NOT NULL,
                    status TEXT NOT NULL, -- 'pending', 'funded', 'cancelled'
                    breakdown_json TEXT NOT NULL,
                    stripe_payment_intent_id TEXT,
                    created_at TEXT NOT NULL,
                    resolved_at TEXT
                );
                """
            )

    # ── Balance & Ledger Operations ───────────────────────────────────────────

    def get_balance(self, workspace_id: str) -> Dict[str, Any]:
        """Retrieve current credit balance for workspace."""
        with closing(self._get_connection()) as conn:
            row = conn.execute(
                "SELECT balance_usd, currency, tier, updated_at "
                "FROM workspace_credits WHERE workspace_id = ?",
                (workspace_id,),
            ).fetchone()
            if not row:
                return {
                    "workspace_id": workspace_id,
                    "balance_usd": 0.0,
                    "currency": "usd",
                    "tier": "standard",
                    "updated_at": _utc_now_iso(),
                }
            return {
                "workspace_id": workspace_id,
                "balance_usd": float(row["balance_usd"]),
                "currency": row["currency"],
                "tier": row["tier"],
                "updated_at": row["updated_at"],
            }

    def credit_balance(
        self,
        workspace_id: str,
        amount_usd: float,
        kind: str = "topup",
        reference_id: Optional[str] = None,
        description: str = "",
    ) -> Dict[str, Any]:
        """Add credits to workspace (e.g. after Stripe webhook confirmation)."""
        if amount_usd <= 0:
            raise ValueError("Credit amount must be greater than zero")

        now = _utc_now_iso()
        tx_id = f"tx_{uuid.uuid4().hex[:12]}"

        with closing(self._get_connection()) as conn, conn:
            row = conn.execute(
                "SELECT balance_usd FROM workspace_credits WHERE workspace_id = ?",
                (workspace_id,),
            ).fetchone()
            current_balance = float(row["balance_usd"]) if row else 0.0
            new_balance = round(current_balance + amount_usd, 4)

            conn.execute(
                """
                INSERT INTO workspace_credits (
                    workspace_id, balance_usd, currency, tier, updated_at
                ) VALUES (?, ?, 'usd', 'standard', ?)
                ON CONFLICT(workspace_id) DO UPDATE SET
                    balance_usd = excluded.balance_usd,
                    updated_at = excluded.updated_at
                """,
                (workspace_id, new_balance, now),
            )

            conn.execute(
                """
                INSERT INTO credit_transactions (
                    id, workspace_id, amount_usd, balance_after, kind,
                    reference_id, description, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tx_id,
                    workspace_id,
                    amount_usd,
                    new_balance,
                    kind,
                    reference_id,
                    description,
                    now,
                ),
            )

        return {
            "success": True,
            "workspace_id": workspace_id,
            "transaction_id": tx_id,
            "added_usd": amount_usd,
            "balance_usd": new_balance,
        }

    def deduct_credits(
        self,
        workspace_id: str,
        amount_usd: float,
        task_id: str,
        description: str = "",
    ) -> bool:
        """Deduct credits when an agent executes a paid task.

        Returns False if insufficient funds.
        """
        if amount_usd <= 0:
            return True

        now = _utc_now_iso()
        tx_id = f"tx_{uuid.uuid4().hex[:12]}"

        with closing(self._get_connection()) as conn, conn:
            row = conn.execute(
                "SELECT balance_usd FROM workspace_credits WHERE workspace_id = ?", (workspace_id,)
            ).fetchone()
            current_balance = float(row["balance_usd"]) if row else 0.0

            if current_balance < amount_usd:
                return False

            new_balance = round(current_balance - amount_usd, 4)
            conn.execute(
                """
                UPDATE workspace_credits
                SET balance_usd = ?, updated_at = ?
                WHERE workspace_id = ?
                """,
                (new_balance, now, workspace_id),
            )
            conn.execute(
                """
                INSERT INTO credit_transactions (
                    id, workspace_id, amount_usd, balance_after, kind,
                    reference_id, description, created_at
                ) VALUES (?, ?, ?, ?, 'task_deduction', ?, ?, ?)
                """,
                (tx_id, workspace_id, -amount_usd, new_balance, task_id, description, now),
            )
            return True

    # ── Task Cost Calculation & Quotes ────────────────────────────────────────

    def calculate_task_quote(self, task: Dict[str, Any], agent_type: str) -> Dict[str, Any]:
        """
        Calculate realistic cost estimation for a task:
        - Base model tokens (input/output)
        - Tool & third-party API fees (e.g. search, scraping, deployment)
        - Platform execution markup
        """
        raw_budget = float(task.get("estimated_budget") or task.get("budget") or 0.0)
        days = int(task.get("estimated_days") or task.get("timeline_days") or 1)

        # Baseline per-agent tool requirements
        tool_rates = {
            "researcher": {"api_name": "Serper & Web Scraping", "cost": 0.25},
            "branding": {"api_name": "Asset & SVG Generation", "cost": 0.35},
            "web_development": {"api_name": "Sandbox & Cloud Hosting", "cost": 0.50},
            "martech": {"api_name": "SEO & Domain Analytics API", "cost": 0.30},
            "campaigns": {"api_name": "Ad & Outreach Integrations", "cost": 0.40},
            "legal": {"api_name": "Regulatory & Entity Verification", "cost": 0.45},
            "cto": {"api_name": "Cloud Architecture & Spec Engine", "cost": 0.30},
            "cfo": {"api_name": "Financial Modeling & Tax Tables", "cost": 0.20},
        }

        tool_meta = tool_rates.get(
            agent_type.lower(),
            {"api_name": "Standard Tools", "cost": 0.15},
        )

        # Calculate granular components
        estimated_tokens = 30000 + (days * 2000)
        # Assuming typical GPT-4o-mini rates: $0.15/1M input, $0.60/1M output
        token_cost = round((estimated_tokens * 0.0000006), 4)
        api_tools_cost = tool_meta["cost"]
        platform_fee = 0.20  # baseline orchestration fee

        total_quote = round(token_cost + api_tools_cost + platform_fee, 2)

        return {
            "task_id": task.get("task_id", "task"),
            "agent_type": agent_type,
            "total_quoted_usd": total_quote,
            "scenario_budget_reference": raw_budget,
            "breakdown": {
                "estimated_tokens": estimated_tokens,
                "token_cost_usd": token_cost,
                "tool_service": tool_meta["api_name"],
                "tool_cost_usd": api_tools_cost,
                "platform_fee_usd": platform_fee,
            },
        }

    # ── Stripe Payment Intent Generation ──────────────────────────────────────

    def create_stripe_checkout_session(
        self,
        workspace_id: str,
        amount_usd: float,
        task_id: Optional[str] = None,
        success_url: str = "http://localhost:5001/?payment=success",
        cancel_url: str = "http://localhost:5001/?payment=cancelled",
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout Session or mocked session if Stripe API key is not configured.
        """
        stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
        amount_cents = int(round(amount_usd * 100))

        if stripe_key and not stripe_key.startswith("mock_"):
            try:
                import stripe

                stripe.api_key = stripe_key
                session = stripe.checkout.Session.create(
                    payment_method_types=["card"],
                    line_items=[
                        {
                            "price_data": {
                                "currency": "usd",
                                "product_data": {
                                    "name": f"Agent Execution Credits ({task_id or 'Top-up'})",
                                    "description": (
                                        "Dedicated compute and API credits for autonomous task "
                                        f"{task_id or 'workspace'}"
                                    ),
                                },
                                "unit_amount": amount_cents,
                            },
                            "quantity": 1,
                        }
                    ],
                    mode="payment",
                    success_url=success_url + "&session_id={CHECKOUT_SESSION_ID}",
                    cancel_url=cancel_url,
                    metadata={"workspace_id": workspace_id, "task_id": task_id or ""},
                )
                return {
                    "mode": "live",
                    "checkout_url": session.url,
                    "session_id": session.id,
                    "amount_usd": amount_usd,
                }
            except Exception as e:
                logger.error(f"Stripe session creation failed: {e}")
                # Fall through to sandbox checkout mode

        # Mock / Sandbox checkout session for development and non-production testing
        mock_session_id = f"cs_test_{uuid.uuid4().hex}"
        mock_checkout_url = (
            f"/api/billing/mock-checkout?session_id={mock_session_id}"
            f"&amount={amount_usd}&workspace={workspace_id}&task_id={task_id or ''}"
        )

        return {
            "mode": "sandbox",
            "checkout_url": mock_checkout_url,
            "session_id": mock_session_id,
            "amount_usd": amount_usd,
            "note": "Running in sandbox mode. Set STRIPE_SECRET_KEY for live processing.",
        }


# Singleton service instance
billing_service = BillingService()
