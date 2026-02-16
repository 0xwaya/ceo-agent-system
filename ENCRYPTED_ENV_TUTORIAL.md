# Encrypted Environment Configuration

## 🔐 Secure API Key Management for Multi-Agent System

This tutorial demonstrates how to securely store and manage API keys and sensitive configuration data for your multi-agent system.

---

## 📚 Table of Contents

1. [Why Encryption?](#why-encryption)
2. [Security Architecture](#security-architecture)
3. [Quick Start](#quick-start)
4. [Detailed Guide](#detailed-guide)
5. [Production Deployment](#production-deployment)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Why Encryption

### The Problem
- **Exposed Secrets**: API keys in plain text `.env` files
- **Version Control Risk**: Accidentally committing credentials to Git
- **Collaboration Issues**: Sharing credentials insecurely
- **Compliance**: Security requirements for data protection

### The Solution
- ✅ **Encrypted Storage**: API keys encrypted at rest
- ✅ **Safe Collaboration**: Commit encrypted files to Git
- ✅ **Key Separation**: Encryption keys stored separately
- ✅ **Industry Standard**: Uses Fernet (AES 128-bit) encryption

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   DEVELOPMENT WORKFLOW                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. CREATE .env with API keys      (SECRET - local only)   │
│  2. GENERATE .env.key              (SECRET - secure vault)  │
│  3. ENCRYPT → .env.encrypted       (SAFE - commit to Git)  │
│  4. DISTRIBUTE .env.key securely   (1Password, AWS Secrets) │
│  5. DECRYPT on deployment          (Production servers)    │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Files:
┌──────────────────┬─────────────────┬──────────────────────┐
│ File             │ Commit to Git?  │ Description          │
├──────────────────┼─────────────────┼──────────────────────┤
│ .env             │ ❌ NO           │ Plain text secrets   │
│ .env.key         │ ❌ NO           │ Encryption key       │
│ .env.encrypted   │ ✅ YES          │ Encrypted secrets    │
│ .gitignore       │ ✅ YES          │ Protects .env files  │
└──────────────────┴─────────────────┴──────────────────────┘
```

---

## Quick Start

### Before You Begin (Recommended)

Use your project virtual environment and confirm command access first:

```bash
cd /Users/pc/code/langraph
source .venv/bin/activate
python3 tools/encrypted_env_demo.py show
```

If this is your first encrypted setup in this repo, continue below.

### Step 0: Safety Check (One-Time)

```bash
# Confirm sensitive files are ignored
grep -E "^\.env$|^\.env\.key$|^\*\.key$" .gitignore

# Optional: verify current git view before changes
git status
```

Expected: `.env` and `.env.key` are ignored, while `.env.encrypted` is safe to commit.

### Step 1: Initial Setup
```bash
# Generate encryption key and sample .env file
python3 tools/encrypted_env_demo.py setup
```

**Output:**
```
✓ Generated encryption key: .env.key
  ⚠️  IMPORTANT: Store this key securely
  ⚠️  NEVER commit .env.key to version control!
✓ Created sample .env file: .env
  → Edit this file with your actual API keys
```

### Step 2: Edit Configuration
```bash
# Edit .env with your real API keys
nano .env
```

> Note: You wrote `.evn` in chat, but the correct filename is `.env`.

**Example `.env` content:**
```bash
# OpenAI API
OPENAI_API_KEY=sk-proj-abc123...
OPENAI_CODEX_ENABLED=true
OPENAI_CODEX_MODEL=gpt-5-codex
OPENAI_CODEX_TIMEOUT_SECONDS=45

# Anthropic Claude API
ANTHROPIC_API_KEY=sk-ant-xyz789...

# Flask Configuration
SECRET_KEY=your-super-secret-key-2026

# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

### Step 3: Encrypt
```bash
# Encrypt your .env file
python3 tools/encrypted_env_demo.py encrypt
```

**Output:**
```
✓ Encrypted .env → .env.encrypted
  Size: 847 bytes → 1184 bytes
📋 Safe to commit: .env.encrypted
```

### Step 3.5: Validate Encryption State

```bash
python3 tools/encrypted_env_demo.py show
```

You should see:
- `.env.key` exists (do not commit)
- `.env` exists (do not commit)
- `.env.encrypted` exists (safe to commit)

### Step 4: Commit to Git
```bash
git add .env.encrypted .gitignore
git commit -m "Add encrypted environment configuration"
git push
```

### Step 5: Runtime Validation (Important)

Confirm the app can load encrypted values on startup:

```bash
# Optional dry run for decrypt
python3 tools/encrypted_env_demo.py decrypt

# Start app and verify no env-loading errors
python3 app.py
```

If `.env` is missing but `.env.encrypted` and `.env.key` are present, the app bootstrap will attempt decrypt/load automatically.

### Rollback / Recovery

If you encrypt with the wrong key or wrong values:

```bash
# Re-edit plaintext
nano .env

# Re-encrypt with current key
python3 tools/encrypted_env_demo.py encrypt

# Re-check status
python3 tools/encrypted_env_demo.py show
```

---

## Detailed Guide

### View Configuration Status
```bash
python3 tools/encrypted_env_demo.py show
```

**Output:**
```
📊 Encrypted Environment Configuration Status
============================================================
Project root: /Users/pc/code/langraph

Files:
  .env.key:       ✓ EXISTS (DO NOT COMMIT)
  .env:           ✓ EXISTS (DO NOT COMMIT)
  .env.encrypted: ✓ EXISTS (SAFE TO COMMIT)

Environment variables: 15 configured

📋 Recommendations:
   ✓ Configuration is properly encrypted
```

### Decrypt for Use
```bash
# On production server or new development machine
python3 tools/encrypted_env_demo.py decrypt
```

### Using in Your Application
```python
# Load encrypted environment variables
from tools.encrypted_env_demo import EncryptedEnvManager

# Initialize manager
env_manager = EncryptedEnvManager()

# Load and decrypt environment variables
env_vars = env_manager.load_env(decrypt_first=True)

# Access variables
openai_key = env_vars.get('OPENAI_API_KEY')
# or from os.environ
import os
openai_key = os.getenv('OPENAI_API_KEY')
```

---

## Production Deployment

### Option 1: AWS Secrets Manager
```bash
# Store encryption key in AWS Secrets Manager
aws secretsmanager create-secret \
  --name langraph-env-key \
  --secret-string file://.env.key

# Retrieve in production
aws secretsmanager get-secret-value \
  --secret-id langraph-env-key \
  --query SecretString \
  --output text > .env.key
```

### Option 2: Docker Secrets
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Copy encrypted env file (safe in image)
COPY .env.encrypted /app/.env.encrypted

# Copy requirements
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

# Encryption key will be mounted as secret at runtime
COPY tools/ /app/tools/
WORKDIR /app

# Decrypt on container startup
RUN --mount=type=secret,id=env_key \
    cp /run/secrets/env_key .env.key && \
    python3 tools/encrypted_env_demo.py decrypt

CMD ["python3", "app.py"]
```

### Option 3: GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Decrypt environment
        env:
          ENV_KEY: ${{ secrets.ENV_ENCRYPTION_KEY }}
        run: |
          echo "$ENV_KEY" > .env.key
          python3 tools/encrypted_env_demo.py decrypt

      - name: Deploy application
        run: |
          # Your deployment commands here
```

---

## Best Practices

### 🔒 Security
1. **Never Commit**:
   - ❌ `.env` (plaintext secrets)
   - ❌ `.env.key` (encryption key)
   - ❌ `*.key` files

2. **Always Commit**:
   - ✅ `.env.encrypted` (encrypted secrets)
   - ✅ `.gitignore` (protection rules)
   - ✅ `tools/encrypted_env_demo.py` (encryption tool)

3. **Key Storage**:
   - Use password managers (1Password, LastPass)
   - Use cloud secret managers (AWS Secrets Manager, Azure Key Vault)
   - Use CI/CD secret storage (GitHub Secrets, GitLab CI Variables)

### 🔄 Workflow
1. **Rotating Keys**:
   ```bash
   # Generate new key
   python3 tools/encrypted_env_demo.py setup --overwrite

   # Re-encrypt with new key
   python3 tools/encrypted_env_demo.py encrypt

   # Update key in secret manager
   ```

2. **Team Onboarding**:
   ```bash
   # New team member:
   git clone <repository>
   # Request .env.key from team lead (secure channel)
   python3 tools/encrypted_env_demo.py decrypt
   ```

3. **Environment-Specific Configs**:
   ```bash
   # Create different encrypted files
   .env.development.encrypted
   .env.staging.encrypted
   .env.production.encrypted
   ```

---

## API Integration Preparation

### Required vs Optional APIs

The `.env` template includes **comprehensive API examples** for all agent types. However, **not all APIs are required** to get started. Here's what each agent needs:

#### **🔥 CRITICAL (Required for Core Functionality)**
- **OpenAI API** or **Anthropic Claude** - At least one LLM service
- **Flask SECRET_KEY** - Application security

#### **💼 CFO Agent (Orchestrator)**
**Required:**
- LLM API (OpenAI/Claude/Gemini)

**Optional:**
- Analytics APIs for budget tracking
- Project management integrations

#### **🎨 Branding Agent (Logo & Visual Identity)**
**Core:**
- **OpenAI DALL-E** (via OpenAI API) - AI logo generation
- **Stability AI** - Alternative image generation

**Enhanced:**
- Adobe Creative Cloud API - Professional design tools
- Canva API - Quick design automation
- Figma API - Design collaboration
- Unsplash/Pexels - Stock imagery

**Use Cases:**
- Generate 4 logo concepts with AI
- Create brand color palettes
- Design business cards and marketing materials
- Build style guides

#### **💻 Web Development Agent (Websites & AR)**
**Core:**
- **Vercel** or **Netlify** - Deployment platform
- **GitHub API** - Version control

**Enhanced:**
- **Cloudflare** - CDN and security
- **AWS S3** - Asset storage
- **Firebase** - Real-time features
- **8th Wall** or **Zapworks** - WebAR capabilities

**Use Cases:**
- Deploy Next.js websites automatically
- Set up AR countertop visualization
- Configure CDN for global performance
- Implement real-time features

#### **⚖️ Legal Agent (Compliance & Filings)**
**Core:**
- **USPTO API** - Trademark search (free public API)

**Enhanced:**
- **DocuSign** - Electronic signatures
- **LegalZoom** - Business formation services
- State-specific filing APIs

**Use Cases:**
- File DBA (Doing Business As) registration
- Trademark availability search
- Generate operating agreements
- Digital contract signing

#### **📊 Martech Agent (Marketing Technology)**
**Core:**
- **HubSpot** OR **Salesforce** - At least one CRM

**Enhanced:**
- **Google Analytics 4** - Web analytics
- **Mailchimp/SendGrid** - Email marketing
- **Segment** - Customer data platform
- **Zapier/Make** - Workflow automation

**Use Cases:**
- Set up CRM with contact management
- Configure marketing email automation
- Implement website analytics
- Create lead scoring workflows

#### **📸 Content Agent (Media Production & SEO)**
**Core:**
- **YouTube API** or **Vimeo** - Video management
- **Cloudinary** - Media optimization

**Enhanced:**
- **SEMrush/Ahrefs** - SEO research
- **Buffer/Hootsuite** - Social scheduling
- **ElevenLabs** - AI voice-over
- **Grammarly** - Content quality

**Use Cases:**
- Generate video content for YouTube
- Optimize images for web performance
- Research SEO keywords
- Schedule social media posts
- Create AI voice-overs

#### **🚀 Campaigns Agent (Advertising & Paid Media)**
**Core:**
- **Google Ads API** - Search advertising
- **Facebook Ads API** - Social advertising

**Enhanced:**
- **LinkedIn Ads** - B2B campaigns
- **TikTok Ads** - Short-form video
- **Twitter/X Ads** - Social engagement
- **Google Tag Manager** - Analytics tracking
- **Branch.io** - Attribution tracking

**Use Cases:**
- Launch Google Search campaigns
- Create Facebook/Instagram ads
- Set up conversion tracking
- Manage multi-channel attribution
- Optimize ad spend with AI

---

### API Cost Considerations

Most services offer **free tiers** perfect for development and testing:

| Service | Free Tier | Monthly Cost (Paid) |
|---------|-----------|---------------------|
| OpenAI | $5 credit | ~$20-200 (pay-as-you-go) |
| Anthropic Claude | Limited free | ~$20-200 (usage-based) |
| Vercel | Generous free tier | $20+ (Pro) |
| GitHub | Unlimited public repos | Free for teams |
| Cloudinary | 25GB storage | $99+ (Plus) |
| HubSpot | Free CRM | $45+ (Starter) |
| Mailchimp | 500 contacts | $13+ (Essentials) |
| Google Analytics | Free | Free |
| Canva | Free templates | $13/month (Pro) |

**Recommendation:** Start with free tiers, upgrade as you scale.

---

## API Setup Priority

### Phase 1: Core Setup (Day 1)
```bash
# Minimum viable configuration
OPENAI_API_KEY=sk-...           # AI generation
SECRET_KEY=random-string         # App security
FLASK_ENV=development           # Environment
```

### Phase 2: Agent Basics (Week 1)
```bash
# Enable basic agent functionality
VERCEL_TOKEN=...                # Web deployment
GITHUB_TOKEN=...                # Code management
HUBSPOT_API_KEY=...            # Basic CRM
GOOGLE_ANALYTICS_ID=...         # Web analytics
```

### Phase 3: Full Integration (Month 1)
```bash
# Complete agent capabilities
STABILITY_API_KEY=...           # Branding: AI images
CLOUDINARY_CLOUD_NAME=...       # Content: Media optimization
GOOGLE_ADS_CLIENT_ID=...        # Campaigns: Advertising
FACEBOOK_ACCESS_TOKEN=...       # Campaigns: Social ads
DOCUSIGN_INTEGRATION_KEY=...    # Legal: E-signatures
```

### Phase 4: Advanced Features (Month 2+)
```bash
# Professional-grade integrations
SALESFORCE_CLIENT_ID=...        # Enterprise CRM
SEMRUSH_API_KEY=...            # Advanced SEO
DATADOG_API_KEY=...            # Monitoring
SENTRY_DSN=...                 # Error tracking
```

---

## Supported Services

The encrypted `.env` supports integration with:

### **AI/LLM Services**
- **OpenAI** (GPT-4, GPT-3.5): `OPENAI_API_KEY`
- **Anthropic** (Claude): `ANTHROPIC_API_KEY`
- **Google** (Gemini): `GOOGLE_API_KEY`
- **Cohere**: `COHERE_API_KEY`

#### **Marketing & Analytics**
- **Google Analytics**: `GOOGLE_ANALYTICS_ID`
- **Facebook/Meta**: `FACEBOOK_ACCESS_TOKEN`
- **HubSpot**: `HUBSPOT_API_KEY`
- **Mailchimp**: `MAILCHIMP_API_KEY`

#### **CRM & Sales**
- **Salesforce**: `SALESFORCE_CLIENT_ID`, `SALESFORCE_CLIENT_SECRET`
- **Pipedrive**: `PIPEDRIVE_API_KEY`

#### **Payment Processing**
- **Stripe**: `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET`
- **PayPal**: `PAYPAL_CLIENT_ID`, `PAYPAL_SECRET`

#### **Communication**
- **SendGrid**: `SENDGRID_API_KEY`
- **Twilio**: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`

---

## Troubleshooting

### Problem: "Encryption key not found"
```bash
# Solution: Run setup to generate key
python3 tools/encrypted_env_demo.py setup
```

### Problem: "Decryption failed"
```bash
# Cause: Wrong encryption key or corrupted file

# Solution 1: Verify you have the correct .env.key
# Solution 2: Re-encrypt from source .env
python3 tools/encrypted_env_demo.py encrypt
```

### Problem: "Module 'cryptography' not found"
```bash
# Solution: Install dependency
pip install cryptography

# Or install all requirements
pip install -r requirements.txt
```

### Problem: Accidentally committed `.env`
```bash
# Remove from Git history
git rm --cached .env
git commit -m "Remove accidentally committed .env"

# Regenerate encryption key (old one is compromised)
python3 tools/encrypted_env_demo.py setup --overwrite
python3 tools/encrypted_env_demo.py encrypt
```

---

## Complete Example Workflow

### Developer Workflow
```bash
# Day 1: Setup
cd /Users/pc/code/langraph
python3 tools/encrypted_env_demo.py setup
nano .env  # Add real API keys
python3 tools/encrypted_env_demo.py encrypt
git add .env.encrypted
git commit -m "Add encrypted environment"
git push

# Day 2: New machine
git clone <repo>
# (Get .env.key from secure storage)
python3 tools/encrypted_env_demo.py decrypt
python3 app.py  # App loads environment variables
```

### Production Server Deployment
```bash
# On production server
git pull
python3 -c "import boto3; print(boto3.client('secretsmanager').get_secret_value(SecretId='env-key')['SecretString'])" > .env.key
python3 tools/encrypted_env_demo.py decrypt
python3 app.py
```

---

## Next Steps

1. ✅ Set up encryption: `python3 tools/encrypted_env_demo.py setup`
2. ✅ Add your API keys to `.env`
3. ✅ Encrypt: `python3 tools/encrypted_env_demo.py encrypt`
4. ✅ Store `.env.key` in password manager
5. ✅ Commit `.env.encrypted` to Git
6. 🚀 Deploy with confidence!

---

**Security Note**: This encryption method protects against accidental exposure in version control. For production systems handling sensitive data, combine this with:
- Infrastructure-level security (VPCs, firewalls)
- Access control (IAM roles, RBAC)
- Audit logging
- Regular security audits
- Key rotation policies
