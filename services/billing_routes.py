"""Browser billing APIs and the separately authenticated Stripe webhook."""

import logging
from flask import Blueprint, g, jsonify, request
import stripe
import click
from urllib.parse import urlsplit

from services.billing_service import BillingUnavailable, billing_service

logger = logging.getLogger(__name__)


def billing_blueprint(owner_getter, protect):
    bp = Blueprint("billing", __name__)

    @bp.cli.command("reconcile")
    @click.option("--workspace", required=True)
    @click.option("--topup-usd", required=True)
    def reconcile(workspace, topup_usd):
        """Operator-only recovery after reviewing a refund/dispute and ledger."""
        click.confirm(
            "Confirm Stripe refund/dispute review is complete and this balance is correct",
            abort=True,
        )
        try:
            billing_service.reconcile(workspace, topup_usd)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        click.echo("Billing resumed with the reconciled top-up balance and no monthly credits.")

    @bp.errorhandler(ValueError)
    def invalid(exc):
        logger.warning("Invalid billing request: %s", exc)
        return jsonify(success=False, error=str(exc)), 400

    @bp.errorhandler(BillingUnavailable)
    def unavailable(exc):
        logger.error("Billing configuration unavailable: %s", exc)
        return jsonify(success=False, error=str(exc)), 503

    @bp.errorhandler(stripe.StripeError)
    def stripe_error(exc):
        logger.error("Stripe request failed (%s)", type(exc).__name__)
        return jsonify(success=False, error="Stripe request failed. Please retry later."), 502

    def body():
        data = request.get_json()
        if not isinstance(data, dict):
            raise ValueError("Request body must be a JSON object")
        return data

    def payment_ready():
        if not billing_service.enabled():
            raise BillingUnavailable("Membership billing is disabled")
        settings = billing_service.settings()
        if request.host != urlsplit(settings["origin"]).netloc:
            raise BillingUnavailable(
                f"Open the dashboard at {settings['origin']} before starting a payment"
            )
        if settings["live"] and not getattr(g, "account", None):
            raise BillingUnavailable("Live payments require named-account authentication")

    @bp.get("/api/billing/balance")
    @protect
    def balance():
        return jsonify(success=True, **billing_service.get_balance(owner_getter()))

    @bp.get("/api/billing/plans")
    @protect
    def plans():
        settings = billing_service.settings()
        return jsonify(
            success=True,
            membership={
                "name": "WayaLabs AI Membership",
                "price_usd": settings["price"] / 100,
                "included_usd": settings["allowance"] / 100,
                "interval": "month",
                "rollover": False,
            },
            sandbox=not settings["live"],
        )

    @bp.post("/api/billing/quote")
    @protect
    def quote():
        data = body()
        return jsonify(
            success=True,
            quote=billing_service.calculate_task_quote(
                data.get("task", {}), data.get("agent_type", "researcher")
            ),
        )

    @bp.post("/api/billing/checkout")
    @protect
    def checkout():
        payment_ready()
        data = body()
        return jsonify(
            success=True,
            checkout=billing_service.create_checkout(
                owner_getter(), data.get("kind", "membership"), data.get("amount_cents")
            ),
        )

    @bp.post("/api/billing/portal")
    @protect
    def portal():
        payment_ready()
        if body():
            raise ValueError("Portal accepts no customer or redirect overrides")
        return jsonify(success=True, url=billing_service.create_portal(owner_getter()))

    @bp.post("/api/billing/webhook")
    def webhook():
        try:
            event = billing_service.verify_event(
                request.get_data(cache=True), request.headers.get("Stripe-Signature", "")
            )
        except (ValueError, stripe.SignatureVerificationError):
            logger.warning("Rejected invalid Stripe webhook signature or payload")
            return jsonify(success=False, error="Invalid Stripe webhook"), 400
        billing_service.handle_event(event)
        return jsonify(success=True)

    return bp
