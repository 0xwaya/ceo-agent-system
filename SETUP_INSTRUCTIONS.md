# 🚀 Real-World Task Execution - Setup Instructions

## Quick Start (5 Minutes)

### Step 1: Install Required Packages

```bash
cd /Users/pc/code/langraph

# Install OpenAI package
pip install openai==1.12.0

# Install LangChain packages
pip install langchain==0.1.0 langchain-openai==0.0.5

# Install utilities
pip install python-dotenv tiktoken

# Update requirements
pip freeze > requirements.txt
```

### Step 2: Get Your OpenAI API Key

1. Go to: https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-proj-...`)

**Pricing:**
- DALL-E 3: $0.04 per image (standard) or $0.08 (HD)
- GPT-4 Turbo: $10 per 1M input tokens, $30 per 1M output tokens
- GPT-3.5 Turbo: $0.50 per 1M input tokens, $1.50 per 1M output tokens

**Free Credits:**
- New accounts get $5 in free credits
- Enough for ~125 logo generations or ~50k GPT-4 tokens

### Step 3: Configure Environment Variables

```bash
# Create or edit .env file
nano .env

# Add these lines (replace with your actual key):
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Save and exit (Ctrl+X, then Y, then Enter)
```

### Step 4: Test Your First Real Task

```bash
# Quick test: Generate a real logo
python3 tools/quick_start_dalle.py
```

**Expected Output:**
```
================================================================================
🎨 QUICK START: REAL LOGO GENERATION
================================================================================

✅ API Key found: sk-proj-ABC123...
✅ OpenAI client initialized

📋 Logo Brief:
   Company: Surfacecraft Studio
   Industry: Granite & Countertop Installation
   Style: Modern, minimalist
   Colors: Navy blue + warm gray

🎨 Generating logo with DALL-E 3...
   Cost: $0.04 (standard quality, 1024x1024)

✅ Logo generated successfully!

🖼️  Image URL:
   https://oaidalleapiprodscus.blob.core.windows.net/private/...

📊 Task Summary:
   ✅ Task: Logo generation
   ✅ Tool: OpenAI DALL-E 3
   ✅ Cost: $0.04
   ✅ Output: https://oaidalleapiprodscus...
```

**Your agent just executed its first real-world task! 🎉**

---

## Next: Add More Capabilities

### Option A: Add Email Sending (SendGrid)

```bash
# Install SendGrid
pip install sendgrid

# Get API key: https://app.sendgrid.com/settings/api_keys
# Add to .env:
SENDGRID_API_KEY=SG.your-key-here
SENDGRID_FROM_EMAIL=your-verified-email@example.com
```

**Free Tier:** 100 emails/day forever

### Option B: Add Social Media Posting (Twitter)

```bash
# Install Tweepy
pip install tweepy

# Get API keys: https://developer.twitter.com/en/portal/dashboard
# Add to .env:
TWITTER_API_KEY=your-api-key
TWITTER_API_SECRET=your-api-secret
TWITTER_ACCESS_TOKEN=your-access-token
TWITTER_ACCESS_SECRET=your-access-secret
```

**Cost:** $100/month for Basic tier (3,000 posts/month)

### Option C: Add Calendar Control (Google Calendar)

```bash
# Install Google Client Library
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

# Follow OAuth setup: https://developers.google.com/calendar/api/quickstart/python
```

**Free:** Unlimited API calls to your own Google Calendar

### Option D: Add File Storage (AWS S3)

```bash
# Install boto3
pip install boto3

# Get AWS credentials: https://console.aws.amazon.com/iam/
# Add to .env:
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket-name
```

**Free Tier:** 5GB storage, 20,000 GET requests, 2,000 PUT requests/month

---

## Integration Checklist

### Essentials (Week 1-2)
- [x] OpenAI DALL-E (Logo generation) - **DONE**
- [ ] OpenAI GPT-4 (LLM reasoning) - Next
- [ ] SendGrid (Email) - Easy win
- [ ] Google Calendar API (Scheduling) - High value

### High Value (Week 3-4)
- [ ] Twitter API v2 (Social posting)
- [ ] LinkedIn API (Professional posts)
- [ ] AWS S3 (File storage)
- [ ] Google Drive API (Document management)

### Advanced (Week 5-8)
- [ ] Zapier/Make.com (Workflow automation)
- [ ] Airtable (Database)
- [ ] Notion API (Knowledge base)
- [ ] Stripe API (Payment processing)

---

## Cost Management Tips

### 1. Start with Free Tiers
```yaml
Free Forever:
  - SendGrid: 100 emails/day
  - Google Calendar: Unlimited
  - HubSpot CRM: Full CRM features
  - Mailchimp: 500 contacts
  - Canva: Basic design tools

Free Trials:
  - OpenAI: $5 credit
  - Anthropic: $5 credit
  - Twilio: $15 credit
```

### 2. Use Cheaper Models First
```python
# GPT-3.5 Turbo is 20x cheaper than GPT-4
# Use for simple tasks:
messages = [{"role": "user", "content": "Write a tweet"}]

# GPT-3.5 Turbo ($0.50/1M tokens)
llm = ChatOpenAI(model="gpt-3.5-turbo")

# GPT-4 only for complex reasoning ($10/1M tokens)
llm = ChatOpenAI(model="gpt-4-turbo-preview")
```

### 3. Set Spending Limits

In `.env`:
```bash
# Daily budget limits (in USD)
DAILY_BUDGET_DESIGN=10.00
DAILY_BUDGET_COMMUNICATION=5.00
DAILY_BUDGET_SOCIAL=20.00
DAILY_BUDGET_LLM=30.00
```

In your code:
```python
def check_budget(category: str, cost: float) -> bool:
    """Check if spending is within daily limit"""
    daily_limit = float(os.getenv(f"DAILY_BUDGET_{category.upper()}", 0))
    daily_spent = get_daily_spending(category)  # Track in DB

    if daily_spent + cost > daily_limit:
        raise BudgetExceededError(
            f"Daily budget exceeded for {category}: "
            f"${daily_spent + cost} > ${daily_limit}"
        )

    return True
```

### 4. Monitor Usage

```bash
# Check OpenAI usage
# https://platform.openai.com/usage

# Check SendGrid usage
# https://app.sendgrid.com/statistics

# Check AWS usage
# https://console.aws.amazon.com/billing/
```

---

## Testing Your Setup

### Test 1: Logo Generation
```bash
python3 tools/quick_start_dalle.py
```
**Expected:** Logo URL returned, cost = $0.04

### Test 2: LLM Integration
```bash
python3 tests/test_llm_integration.py
```
**Expected:** GPT-4 response to branding/legal questions

### Test 3: Full Agent Execution
```bash
# Run Flask app
python3 app.py

# In browser: http://localhost:5001
# Click "Execute" on Branding Agent
# Verify: Real logo URL in deliverables
```

---

## Troubleshooting

### Error: "No module named 'openai'"
```bash
pip install openai==1.12.0
```

### Error: "Invalid API key"
```bash
# Check .env file has correct key
cat .env | grep OPENAI_API_KEY

# Verify key starts with 'sk-proj-' or 'sk-'
```

### Error: "Insufficient credits"
```bash
# Check your OpenAI balance
# https://platform.openai.com/account/billing/overview

# Add payment method if needed
```

### Error: "Rate limit exceeded"
```bash
# OpenAI free tier limits:
# - 3 images/minute (DALL-E)
# - 3 requests/minute (GPT-4)
# - 60 requests/minute (GPT-3.5)

# Solution: Add a delay between requests
import time
time.sleep(30)  # Wait 30 seconds
```

---

## Production Checklist

Before deploying to production:

### Security ✅
- [ ] API keys in environment variables (not hard-coded)
- [ ] `.env` file in `.gitignore`
- [ ] Rotate API keys every 90 days
- [ ] Use least-privilege API scopes
- [ ] Enable 2FA on all service accounts

### Monitoring ✅
- [ ] Cost tracking per tool
- [ ] Daily spending alerts
- [ ] Error logging (Sentry/LogRocket)
- [ ] Uptime monitoring (UptimeRobot)
- [ ] API rate limit tracking

### Reliability ✅
- [ ] Retry logic for failed API calls
- [ ] Circuit breakers for flaky services
- [ ] Fallback providers (GPT-4 → GPT-3.5)
- [ ] Queue system for long tasks (Celery/Redis)
- [ ] Database for state persistence

### Compliance ✅
- [ ] GDPR compliance (data deletion)
- [ ] CAN-SPAM compliance (email unsubscribe)
- [ ] API terms of service review
- [ ] Data retention policies
- [ ] Privacy policy updated

---

## Getting Help

### Documentation
- OpenAI API Docs: https://platform.openai.com/docs
- LangChain Docs: https://python.langchain.com/docs
- LangGraph Docs: https://langchain-ai.github.io/langgraph/

### Community
- LangChain Discord: https://discord.gg/langchain
- OpenAI Forum: https://community.openai.com/
- Stack Overflow: Tag `langchain` or `openai-api`

### Support
- OpenAI Support: https://help.openai.com/
- LangChain Issues: https://github.com/langchain-ai/langchain/issues

---

## What's Next

1. ✅ **You've completed:** Logo generation with DALL-E
2. 🎯 **Next task:** Integrate GPT-4 for LLM reasoning
3. 📧 **Then:** Add email sending with SendGrid
4. 📅 **Then:** Add calendar integration
5. 🚀 **Finally:** Full autonomous agent execution

**Your agents are now capable of real-world task execution!** 🎉

Continue with the [Real-World Execution Roadmap](docs/REAL_WORLD_EXECUTION_ROADMAP.md) for the complete implementation guide.
