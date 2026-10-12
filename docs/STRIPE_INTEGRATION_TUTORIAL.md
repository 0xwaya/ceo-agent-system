# Stripe Integration Guide for CEO Agent System

This guide outlines how to set up your Stripe account, retrieve your API credentials, and enable live autonomous credit billing for task execution on the CEO Multi-Agent platform.

---

## 1. Create Your Stripe Account
1. Visit [https://stripe.com](https://stripe.com) and click **Start now** / **Sign Up**.
2. Complete account registration and email verification.
3. You will immediately have access to **Stripe Test Mode** (sandbox), which allows simulating real payments with test credit cards without transferring real money.

---

## 2. Obtain Your Stripe API Keys
1. In the Stripe Dashboard, make sure the **Test Mode** toggle (top right) is switched **ON** (or OFF if you are ready for real production money).
2. Navigate to **Developers** → **API keys** ([https://dashboard.stripe.com/test/apikeys](https://dashboard.stripe.com/test/apikeys)).
3. Locate:
   - **Secret key**: Begins with `sk_test_...` (or `sk_live_...` for production).
   - Click **Reveal test key** and copy it.

---

## 3. Configure the CEO Agent System

### Local Development / Testing
In your `.env` file (or terminal session):
```bash
# Add your Stripe secret key
export STRIPE_API_KEY="sk_test_your_secret_key_here"

# Optional: Default currency
export STRIPE_CURRENCY="usd"
```

### Remote Oracle Cloud VCN Instance
SSH into your Oracle instance and update your environment variables or systemd service file:
```bash
ssh -i ~/.ssh/id_rsa ubuntu@<YOUR_ORACLE_PUBLIC_IP>

# Edit ~/.bashrc or application environment file
echo 'export STRIPE_API_KEY="sk_test_your_secret_key_here"' >> ~/.bashrc
source ~/.bashrc
```

---

## 4. Webhook Setup (Optional for Instant Async Callbacks)
1. In the Stripe Dashboard, go to **Developers** → **Webhooks** ([https://dashboard.stripe.com/test/webhooks](https://dashboard.stripe.com/test/webhooks)).
2. Click **Add endpoint**.
3. Endpoint URL: `https://your-domain.com/api/billing/webhook`
4. Select event to listen to: `checkout.session.completed`.
5. Copy the **Signing secret** (`whsec_...`) and configure:
   ```bash
   export STRIPE_WEBHOOK_SECRET="whsec_your_webhook_signing_secret"
   ```

---

## 5. Testing Payments in Sandbox Mode
- When `STRIPE_API_KEY` is not set or in sandbox mode, the platform automatically generates simulated Stripe Checkout sessions that credit your workspace ledger upon confirmation.
- Once you provide a real `sk_test_...` key and install `pip install stripe`, the system seamlessly initiates official Stripe Checkout hosted pages.
- Use Stripe's official test card numbers (e.g., `4242 4242 4242 4242`, any future expiration date, any 3-digit CVC) to test transactions.
