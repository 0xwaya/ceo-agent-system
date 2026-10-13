# WayaLabs Stripe membership setup

## What is integrated

- Stripe-hosted subscription Checkout: **$29/month with $10 of execution allowance**
  (approved sandbox settings, not validated production pricing).
- Eligible customers see Apple Pay; cards are available as fallback. Hosted Checkout
  requires neither Stripe.js nor a publishable key in the browser. Stripe handles
  Apple Pay merchant validation; app-domain registration is needed if switching to
  embedded Checkout/Elements, not for the current hosted integration.
- Verified `invoice.paid` events grant a monthly allowance once per invoice.
  Unused monthly credits reset on renewal and expire at the paid period's end.
- Optional $5/$15/$25 one-time top-ups remain available across renewals.
- Customer Portal supports invoice history, payment-method updates, and cancellation
  at period end. This release has one plan; price/plan upgrades are not enabled.
- Every metered model call reserves its conservative maximum cost before invocation
  and settles provider-reported usage afterward. Concurrent requests cannot overdraw.
  Missing usage/transport failures consume the reservation conservatively and stop
  the operation; this is an estimate requiring operator reconciliation, not a verified
  provider invoice.
- Fixed-precision integer microdollars are used internally. Stripe amounts use cents.
- Sandbox and live ledgers are separate (`data/billing-sandbox.db` and
  `data/billing-live.db`). Historical mock balances in `data/billing.db` are kept
  for reference but are not imported as purchased credits.
- The scenario/project budget never authorizes a card charge. There are no automatic
  overages or automatic top-ups. External ads, domains, hosting, and other purchases
  are not executed or funded by this membership.
- Refund/dispute events pause spending for operator reconciliation; they do not
  automatically refund the user or recover already-consumed credits.
- Simulated checkout has been removed. API errors never grant credits.

## 1. Private environment configuration

### Application endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /api/billing/balance` | Current workspace allowance, membership status and recent credit history |
| `GET /api/billing/plans` | Server-configured monthly price, allowance and sandbox indicator |
| `POST /api/billing/quote` | Display-only task estimate; accepts `task` and `agent_type` |
| `POST /api/billing/checkout` | Hosted subscription (`kind: membership`) or approved top-up (`kind: topup`, `amount_cents: 500/1500/2500`) |
| `POST /api/billing/portal` | Current workspace's customer portal; accepts an empty JSON object |
| `POST /api/billing/webhook` | Raw Stripe payload authenticated by its signature, not browser credentials |

Browser endpoints use the existing account/CSRF protection when authentication is
enabled. Checkout prices, credit amounts, customer ownership and redirects are
server-controlled. `/api/billing/mock-checkout` has been removed.

Install the project's dependencies in its existing virtual environment:

```bash
python -m pip install -r requirements.txt
```

Set these in your private `.env` (never commit or paste credentials into chat):

```dotenv
STRIPE_SECRET_KEY=<sandbox secret key>
STRIPE_WEBHOOK_SECRET=<signing secret for the actual webhook endpoint>
BILLING_ENABLED=true
BILLING_ALLOW_LIVE=false
BILLING_PUBLIC_URL=http://localhost:5001
STRIPE_MEMBERSHIP_AMOUNT_CENTS=2900
STRIPE_MEMBERSHIP_CREDITS_CENTS=1000
API_JOB_MAX_COST_USD=5
API_JOB_MAX_TOKENS=100000
```

The previously configured `STRIPE_API_KEY` remains supported as a secret-key alias;
`STRIPE_SECRET_KEY` takes precedence. A `STRIPE_PUBLISHABLE_KEY` can stay in `.env`
but is not required by this hosted Checkout implementation. Billing defaults on when
a secret key exists unless explicitly disabled with `BILLING_ENABLED=false`.

Configure verified pricing for the exact model using `PRICED_MODEL`,
`MODEL_INPUT_USD_PER_MILLION`, and `MODEL_OUTPUT_USD_PER_MILLION` before agent calls.
The display-only task quote is illustrative; reservations use these configured rates.
No claim is made that the quote guarantees enough allowance for an entire multi-call task.

Use named accounts (`ENABLE_AUTH=true`) for durable customer ownership across browsers,
logout/login, and restarts. Provision accounts using `flask --app app create-account`.
Login-disabled sandbox development uses browser sessions, is localhost-only, and is
not suitable for paying customers. Live billing rejects anonymous browser sessions.

## 2. Configure and verify the sandbox

This command refuses live keys, creates only test resources, and does not submit
payments. It configures the app's sandbox Customer Portal, creates a test membership
Checkout/Portal session, then expires the Checkout and removes its test customer:

```bash
python -m tools.verify_stripe_sandbox --setup-portal --checkout
```

## 3. Webhooks are required, not optional

For localhost testing, install the official Stripe CLI and authenticate it to the
**WayaLabs sandbox**, then run:

The included supervisor can run both the listener and Flask together, using the
configured sandbox key and keeping the listener's signing secret in process memory:

```bash
python -m tools.run_stripe_sandbox
```

Stop any existing app on port 5001 first. Keep this command running while testing.
It supports the CLI on PATH or at `~/.local/bin/stripe`. It never edits `.env`.
For manually managed processes instead, run:

```bash
stripe listen --forward-to http://localhost:5001/api/billing/webhook \
  --events checkout.session.completed,invoice.paid,invoice.payment_failed,customer.subscription.updated,customer.subscription.deleted,charge.refunded,charge.dispute.created
```

The CLI prints a signing secret. Set **that listener's secret** privately as
`STRIPE_WEBHOOK_SECRET`, then restart the Flask app. A dashboard endpoint's signing
secret does not verify CLI-forwarded events. Keep the listener running during testing.
Match the CLI account/sandbox to the API key's sandbox.

For Oracle/public hosting, register this endpoint in Stripe Workbench:

```text
https://<confirmed-application-domain>/api/billing/webhook
```

Subscribe to the same events above and use that endpoint's own signing secret.
The marketing site `wayalabs.com` does not imply that it hosts the Flask application.
Set `BILLING_PUBLIC_URL` to the confirmed app origin, never a user-supplied redirect.
No public endpoint is created automatically by adding credentials to `.env`.

The Oracle sandbox endpoint has been registered at
`https://147.224.168.182/api/billing/webhook`, **disabled pending server/HTTPS readiness**.
Its signing secret is stored in the private local `.env`. The IP did not respond
on ports 443, 80 or 5001 during setup. Before enabling delivery, deploy this code,
configure the server's private signing secret, and establish trusted HTTPS (a domain
with a certificate, or a valid certificate covering the IP). A public IP alone is
not evidence of a working HTTPS endpoint. Local CLI forwarding remains the active
verified sandbox delivery path.

Webhook signature checks use the raw body. Browser login and CSRF are bypassed
only for this exact POST route; Stripe signatures provide its authentication.
Event/invoice deduplication and wallet changes occur in one SQLite transaction.
Neither success redirects nor Checkout completion alone grant subscription credits.

## 4. Run and test

```bash
python app.py
```

Open the dashboard, select **Membership**, then **Subscribe**.
Use the exact `BILLING_PUBLIC_URL` hostname (by default `http://localhost:5001`),
not `127.0.0.1`: browser session cookies are hostname-specific. Checkout/Portal
reject a different hostname so returning from Stripe preserves workspace ownership.
Use Stripe's test card `4242 4242 4242 4242`, a future expiry and any three-digit CVC.
Apple Pay requires an eligible device/browser and configured Wallet; verify its actual
presentation separately on supported Apple hardware.

Verify:

1. Payment grants $10 once, after the webhook; refreshing the return page grants nothing.
2. Resending the event, or delivering another event for the same invoice, grants nothing extra.
3. Cancelling Checkout grants nothing; failed invoices do not replenish the allowance.
4. Paid renewal resets monthly credits; purchased top-ups survive.
5. Cancellation at period end preserves already-paid credits until expiry.
6. Insufficient allowance blocks model calls, including direct API requests.
7. Portal opens for the current workspace, not a client-supplied customer.
8. Refunds/disputes pause spending and appear in credit history.

Generic `stripe trigger` sample events are not sufficient for end-to-end credit tests:
fulfillment must reference the application's actual customer and locally recorded order.
Complete an app-created sandbox Checkout, or use Stripe test clocks for renewal testing.

Offline validation:

```bash
make check PYTHON=.venv/bin/python
node --check static/js/app.js
```

## 5. Refund/dispute reconciliation

Review the Stripe charge and wallet audit history first. Determine the correct remaining
purchased top-up balance, accounting for refunded purchases and consumed credits.
An operator with server-shell access can then run:

```bash
flask --app app billing reconcile --workspace <account-id> --topup-usd <corrected-balance>
```

The command asks for confirmation, records the adjustment, and clears the pause.
Monthly credits remain zero until the next verified eligible paid invoice.
This does not initiate a Stripe refund or cancel a subscription.

## Before live deployment

- Confirm the application domain, HTTPS, named accounts, backups and single-process hosting.
- Set business/support/privacy/refund details on the WayaLabs site and Stripe account.
- Measure costs before publishing membership pricing.
- Resolve tax requirements. Automatic Tax, discounts, trials and prorated plan changes are
  intentionally not enabled: fulfillment currently requires the full configured USD invoice.
- Configure the live portal and webhook separately; sandbox objects/secrets do not carry over.
- Review authentication/onboarding and refund policy before accepting public customers.
- Explicitly enable live payments only after approval with `BILLING_ALLOW_LIVE=true`.
  The sandbox verification tool still refuses all live keys.
- Commit/push application changes, pull them on Oracle, install dependencies there,
  update the server's private environment and restart. Local `.env` changes are not
  automatically deployed to Oracle.

Sources: [Apple Pay](https://docs.stripe.com/apple-pay),
[subscriptions](https://docs.stripe.com/billing/subscriptions/build-subscriptions),
[webhooks](https://docs.stripe.com/webhooks),
[Customer Portal](https://docs.stripe.com/customer-management).
