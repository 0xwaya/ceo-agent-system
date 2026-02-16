"""
Encrypted Environment Configuration Tutorial
=============================================

This module demonstrates how to securely store and load encrypted API keys
and sensitive configuration data for your multi-agent system.

WHY ENCRYPTION?
---------------
- Protect API keys in version control
- Secure credentials in production
- Enable safe collaboration without exposing secrets
- Meet security compliance requirements

WORKFLOW:
---------
1. Create a master encryption key (one-time setup)
2. Encrypt your .env file with sensitive data
3. Commit encrypted .env.encrypted to version control
4. Decrypt on deployment using secure key management

USAGE:
------
# Initial setup
python3 tools/encrypted_env_demo.py setup

# Encrypt your .env file
python3 tools/encrypted_env_demo.py encrypt

# Decrypt for use
python3 tools/encrypted_env_demo.py decrypt

# View current configuration
python3 tools/encrypted_env_demo.py show
"""

from cryptography.fernet import Fernet
from pathlib import Path
import os
import sys
from typing import Dict, Optional
import json


class EncryptedEnvManager:
    """
    Secure environment configuration manager
    Uses Fernet symmetric encryption (AES 128-bit)
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the encrypted environment manager

        Args:
            project_root: Project root directory (defaults to current directory)
        """
        self.project_root = project_root or Path.cwd()
        self.key_file = self.project_root / ".env.key"
        self.env_file = self.project_root / ".env"
        self.encrypted_file = self.project_root / ".env.encrypted"

        # Ensure .gitignore protects sensitive files
        self._update_gitignore()

    def _update_gitignore(self):
        """Ensure .gitignore includes sensitive files"""
        gitignore_path = self.project_root / ".gitignore"
        patterns_to_add = [".env", ".env.key", "*.key", ".env.local", ".env.*.local"]

        existing_patterns = set()
        if gitignore_path.exists():
            existing_patterns = set(gitignore_path.read_text().splitlines())

        new_patterns = [p for p in patterns_to_add if p not in existing_patterns]

        if new_patterns:
            with gitignore_path.open("a") as f:
                f.write("\n# Encrypted environment configuration\n")
                for pattern in new_patterns:
                    f.write(f"{pattern}\n")
            print(f"✓ Updated .gitignore with {len(new_patterns)} patterns")

    def generate_key(self) -> bytes:
        """
        Generate a new encryption key

        Returns:
            Encryption key bytes
        """
        return Fernet.generate_key()

    def setup(self, overwrite: bool = False) -> bool:
        """
        Initial setup: generate encryption key and create sample .env

        Args:
            overwrite: Whether to overwrite existing key

        Returns:
            Success status
        """
        if self.key_file.exists() and not overwrite:
            print(f"❌ Encryption key already exists at {self.key_file}")
            print(
                "   Use --overwrite to regenerate (WARNING: existing encrypted data will be unrecoverable)"
            )
            return False

        # Generate and save encryption key
        key = self.generate_key()
        self.key_file.write_bytes(key)
        self.key_file.chmod(0o600)  # Restrict permissions
        print(f"✓ Generated encryption key: {self.key_file}")
        print(f"  ⚠️  IMPORTANT: Store this key securely (e.g., password manager, secure vault)")
        print(f"  ⚠️  NEVER commit .env.key to version control!")

        # Create sample .env if it doesn't exist
        if not self.env_file.exists():
            sample_env = self._generate_sample_env()
            self.env_file.write_text(sample_env)
            print(f"✓ Created sample .env file: {self.env_file}")
            print(f"  → Edit this file with your actual API keys and credentials")

        print(f"\n📋 Next steps:")
        print(f"   1. Edit {self.env_file} with your real credentials")
        print(f"   2. Run: python3 tools/encrypted_env_demo.py encrypt")
        print(f"   3. Commit .env.encrypted to version control")
        print(f"   4. Store .env.key in secure secrets manager")

        return True

    def _generate_sample_env(self) -> str:
        """Generate sample .env file content with all agent-specific APIs"""
        return """# ============================================================================
# MULTI-AGENT AI SYSTEM - ENVIRONMENT CONFIGURATION
# ============================================================================
# Complete API configuration for all specialized agents
# Edit this file with your actual credentials, then encrypt it
#
# Usage: python3 tools/encrypted_env_demo.py encrypt
# ============================================================================

# ============================================================================
# FLASK APPLICATION SETTINGS
# ============================================================================
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-secure-secret-key-change-this-to-random-string
FLASK_HOST=0.0.0.0
FLASK_PORT=5001

# ============================================================================
# CORE AI/LLM SERVICES (Used by ALL agents)
# ============================================================================

# OpenAI (GPT-4, GPT-3.5-turbo, DALL-E for image generation)
# Get your API key: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
OPENAI_ORG_ID=org-your-organization-id-here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_CODEX_ENABLED=false
OPENAI_CODEX_MODEL=gpt-5-codex
OPENAI_CODEX_TIMEOUT_SECONDS=45

# Anthropic Claude (Alternative LLM - excellent for analysis)
# Get your API key: https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
ANTHROPIC_MODEL=claude-3-opus-20240229

# Google Gemini (Multimodal AI)
# Get your API key: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your-google-gemini-api-key-here
GOOGLE_MODEL=gemini-pro

# Cohere (Embeddings and generation)
# Get your API key: https://dashboard.cohere.com/api-keys
COHERE_API_KEY=your-cohere-api-key-here

# Social platform APIs (for Social Media Agent execution)
META_APP_ID=your-meta-app-id
META_APP_SECRET=your-meta-app-secret
META_ACCESS_TOKEN=your-meta-access-token
TIKTOK_ACCESS_TOKEN=your-tiktok-access-token
LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret
YOUTUBE_API_KEY=your-youtube-api-key

# ============================================================================
# BRANDING AGENT APIs - Logo Design & Visual Identity
# ============================================================================

# Stability AI (Stable Diffusion - Image Generation)
# Get your API key: https://platform.stability.ai/
STABILITY_API_KEY=sk-your-stability-ai-key-here

# DALL-E (Already in OpenAI above)
# Creates logo concepts, brand imagery, visual assets

# Midjourney (Via unofficial API or Discord bot)
# Note: Midjourney doesn't have official API yet (as of 2026)
MIDJOURNEY_API_TOKEN=your-midjourney-token-if-available

# Adobe Creative Cloud API (For design assets)
# Get credentials: https://developer.adobe.com/
ADOBE_CLIENT_ID=your-adobe-client-id
ADOBE_CLIENT_SECRET=your-adobe-client-secret
ADOBE_ACCESS_TOKEN=your-adobe-access-token

# Canva API (Design automation)
# Get your API key: https://www.canva.com/developers/
CANVA_API_KEY=your-canva-api-key-here

# Figma API (Design collaboration & assets)
# Get your token: https://www.figma.com/developers/api
FIGMA_ACCESS_TOKEN=your-figma-personal-access-token

# Pantone Connect API (Color standards)
PANTONE_API_KEY=your-pantone-api-key-here

# Unsplash API (Stock photography for mockups)
# Get your key: https://unsplash.com/developers
UNSPLASH_ACCESS_KEY=your-unsplash-access-key
UNSPLASH_SECRET_KEY=your-unsplash-secret-key

# ============================================================================
# WEB DEVELOPMENT AGENT APIs - Websites & AR Integration
# ============================================================================

# Vercel (Deployment & hosting)
# Get your token: https://vercel.com/account/tokens
VERCEL_TOKEN=your-vercel-deployment-token
VERCEL_ORG_ID=your-vercel-org-id
VERCEL_PROJECT_ID=your-vercel-project-id

# GitHub (Repository management & version control)
# Get your token: https://github.com/settings/tokens
GITHUB_TOKEN=ghp_your-github-personal-access-token
GITHUB_ORG=your-github-organization
GITHUB_REPO=your-repository-name

# Netlify (Alternative deployment)
# Get your token: https://app.netlify.com/user/applications
NETLIFY_AUTH_TOKEN=your-netlify-auth-token
NETLIFY_SITE_ID=your-netlify-site-id

# Cloudflare (CDN, DNS, security)
# Get your API key: https://dash.cloudflare.com/profile/api-tokens
CLOUDFLARE_API_TOKEN=your-cloudflare-api-token
CLOUDFLARE_ZONE_ID=your-cloudflare-zone-id

# AWS (Cloud infrastructure - S3, CloudFront, etc.)
# Get credentials: https://console.aws.amazon.com/iam/
AWS_ACCESS_KEY_ID=AKIA-your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-s3-bucket-name

# Google Cloud (Alternative cloud platform)
# Get credentials: https://console.cloud.google.com/apis/credentials
GOOGLE_CLOUD_PROJECT_ID=your-gcp-project-id
GOOGLE_CLOUD_CREDENTIALS_JSON=path/to/service-account-key.json

# Firebase (Real-time database, auth, hosting)
# Get your config: https://console.firebase.google.com/
FIREBASE_API_KEY=your-firebase-api-key
FIREBASE_AUTH_DOMAIN=your-app.firebaseapp.com
FIREBASE_PROJECT_ID=your-firebase-project-id

# 8th Wall / WebAR APIs (AR experiences)
# Get your key: https://www.8thwall.com/
EIGHTHWALL_API_KEY=your-8thwall-api-key

# Zapworks (WebAR alternative)
ZAPWORKS_API_KEY=your-zapworks-api-key

# ============================================================================
# LEGAL AGENT APIs - Compliance & Business Filings
# ============================================================================

# LegalZoom API (Business formation services)
LEGALZOOM_API_KEY=your-legalzoom-api-key

# USPTO (Trademark search - Public API)
# Documentation: https://developer.uspto.gov/
USPTO_API_KEY=your-uspto-api-key-if-required

# DocuSign (Electronic signatures)
# Get credentials: https://developers.docusign.com/
DOCUSIGN_INTEGRATION_KEY=your-docusign-integration-key
DOCUSIGN_USER_ID=your-docusign-user-id
DOCUSIGN_ACCOUNT_ID=your-docusign-account-id
DOCUSIGN_RSA_PRIVATE_KEY=path/to/docusign-private-key.pem

# HelloSign/Dropbox Sign API
# Get your key: https://app.hellosign.com/api/reference
HELLOSIGN_API_KEY=your-hellosign-api-key

# Contractbook API (Contract management)
CONTRACTBOOK_API_KEY=your-contractbook-api-key

# Rocket Lawyer API
ROCKETLAWYER_API_KEY=your-rocketlawyer-api-key

# State Filing APIs (varies by state)
# Example: Ohio Secretary of State
OHIO_SOS_API_KEY=your-state-filing-api-key

# ============================================================================
# MARTECH AGENT APIs - CRM, Analytics & Automation
# ============================================================================

# HubSpot (All-in-one CRM & marketing)
# Get your key: https://app.hubspot.com/developer/
HUBSPOT_API_KEY=your-hubspot-api-key
HUBSPOT_PORTAL_ID=your-hubspot-portal-id
HUBSPOT_ACCESS_TOKEN=your-hubspot-private-app-token

# Salesforce (Enterprise CRM)
# Get credentials: https://developer.salesforce.com/
SALESFORCE_CLIENT_ID=your-salesforce-connected-app-client-id
SALESFORCE_CLIENT_SECRET=your-salesforce-client-secret
SALESFORCE_USERNAME=your-salesforce-username
SALESFORCE_PASSWORD=your-salesforce-password
SALESFORCE_SECURITY_TOKEN=your-salesforce-security-token
SALESFORCE_INSTANCE_URL=https://your-instance.salesforce.com

# Pipedrive (Sales CRM)
# Get your key: https://pipedrive.readme.io/docs/how-to-find-the-api-token
PIPEDRIVE_API_TOKEN=your-pipedrive-api-token
PIPEDRIVE_COMPANY_DOMAIN=yourcompany.pipedrive.com

# Google Analytics 4 (Web analytics)
# Get credentials: https://console.cloud.google.com/apis/credentials
GOOGLE_ANALYTICS_MEASUREMENT_ID=G-XXXXXXXXXX
GOOGLE_ANALYTICS_PROPERTY_ID=properties/your-property-id
GOOGLE_ANALYTICS_CREDENTIALS=path/to/ga4-credentials.json

# Segment (Customer data platform)
# Get your key: https://app.segment.com/
SEGMENT_WRITE_KEY=your-segment-write-key
SEGMENT_WORKSPACE_ID=your-segment-workspace-id

# Mixpanel (Product analytics)
# Get your token: https://mixpanel.com/settings/project/
MIXPANEL_TOKEN=your-mixpanel-project-token
MIXPANEL_API_SECRET=your-mixpanel-api-secret

# Amplitude (Product analytics)
# Get your key: https://analytics.amplitude.com/
AMPLITUDE_API_KEY=your-amplitude-api-key

# Mailchimp (Email marketing)
# Get your key: https://mailchimp.com/help/about-api-keys/
MAILCHIMP_API_KEY=your-mailchimp-api-key-us1
MAILCHIMP_SERVER_PREFIX=us1
MAILCHIMP_LIST_ID=your-audience-list-id

# SendGrid (Transactional email)
# Get your key: https://app.sendgrid.com/settings/api_keys
SENDGRID_API_KEY=SG.your-sendgrid-api-key

# ActiveCampaign (Marketing automation)
# Get credentials: https://yourcompany.activehosted.com/admin/settings/api.php
ACTIVECAMPAIGN_URL=https://yourcompany.api-us1.com
ACTIVECAMPAIGN_API_KEY=your-activecampaign-api-key

# Zapier (Workflow automation)
# Get your key: https://zapier.com/app/settings/api
ZAPIER_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/your-webhook-url

# Make (Integromat) - Alternative automation
MAKE_WEBHOOK_URL=https://hook.us1.make.com/your-webhook-id

# ============================================================================
# CONTENT AGENT APIs - Video, Photography & SEO
# ============================================================================

# YouTube Data API (Video management)
# Get credentials: https://console.cloud.google.com/apis/credentials
YOUTUBE_API_KEY=your-youtube-data-api-key
YOUTUBE_CLIENT_ID=your-youtube-oauth-client-id
YOUTUBE_CLIENT_SECRET=your-youtube-oauth-client-secret

# Vimeo API (Video hosting alternative)
# Get your token: https://developer.vimeo.com/apps
VIMEO_ACCESS_TOKEN=your-vimeo-access-token
VIMEO_CLIENT_ID=your-vimeo-client-id
VIMEO_CLIENT_SECRET=your-vimeo-client-secret

# Cloudinary (Media management & optimization)
# Get credentials: https://cloudinary.com/console
CLOUDINARY_CLOUD_NAME=your-cloudinary-cloud-name
CLOUDINARY_API_KEY=your-cloudinary-api-key
CLOUDINARY_API_SECRET=your-cloudinary-api-secret

# Pexels API (Stock photography)
# Get your key: https://www.pexels.com/api/
PEXELS_API_KEY=your-pexels-api-key

# Pixabay API (Stock media)
# Get your key: https://pixabay.com/api/docs/
PIXABAY_API_KEY=your-pixabay-api-key

# SEMrush API (SEO & keyword research)
# Get your key: https://www.semrush.com/api-documentation/
SEMRUSH_API_KEY=your-semrush-api-key

# Ahrefs API (SEO analysis)
# Get your token: https://ahrefs.com/api
AHREFS_API_TOKEN=your-ahrefs-api-token

# Moz API (SEO metrics)
# Get credentials: https://moz.com/products/mozscape/access
MOZ_ACCESS_ID=your-moz-access-id
MOZ_SECRET_KEY=your-moz-secret-key

# Grammarly API (Content quality)
# Note: Grammarly Business API access required
GRAMMARLY_CLIENT_ID=your-grammarly-client-id
GRAMMARLY_CLIENT_SECRET=your-grammarly-client-secret

# Buffer (Social media scheduling)
# Get your token: https://buffer.com/developers/api
BUFFER_ACCESS_TOKEN=your-buffer-access-token

# Hootsuite API (Social media management)
# Get credentials: https://developer.hootsuite.com/
HOOTSUITE_CLIENT_ID=your-hootsuite-client-id
HOOTSUITE_CLIENT_SECRET=your-hootsuite-client-secret

# Later (Instagram & visual content scheduling)
LATER_API_KEY=your-later-api-key

# ElevenLabs (AI voice generation for video content)
# Get your key: https://elevenlabs.io/
ELEVENLABS_API_KEY=your-elevenlabs-api-key

# Runway ML (AI video generation)
# Get your key: https://runwayml.com/
RUNWAYML_API_KEY=your-runwayml-api-key

# ============================================================================
# CAMPAIGNS AGENT APIs - Advertising & Paid Media
# ============================================================================

# Google Ads API (Search & display advertising)
# Get credentials: https://developers.google.com/google-ads/api/docs/get-started
GOOGLE_ADS_CLIENT_ID=your-google-ads-client-id
GOOGLE_ADS_CLIENT_SECRET=your-google-ads-client-secret
GOOGLE_ADS_DEVELOPER_TOKEN=your-google-ads-developer-token
GOOGLE_ADS_REFRESH_TOKEN=your-google-ads-refresh-token
GOOGLE_ADS_CUSTOMER_ID=123-456-7890

# Meta/Facebook Ads API (Facebook & Instagram ads)
# Get your token: https://developers.facebook.com/tools/explorer/
FACEBOOK_ACCESS_TOKEN=EAAxxxYourLongLivedAccessTokenxxxZZZ
FACEBOOK_APP_ID=your-facebook-app-id
FACEBOOK_APP_SECRET=your-facebook-app-secret
FACEBOOK_AD_ACCOUNT_ID=act_your-ad-account-id

# LinkedIn Ads API (B2B advertising)
# Get credentials: https://www.linkedin.com/developers/
LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret
LINKEDIN_ACCESS_TOKEN=your-linkedin-access-token
LINKEDIN_AD_ACCOUNT_ID=your-linkedin-ad-account-urn

# Twitter/X Ads API (Twitter advertising)
# Get credentials: https://developer.twitter.com/
TWITTER_API_KEY=your-twitter-api-key
TWITTER_API_SECRET=your-twitter-api-secret
TWITTER_ACCESS_TOKEN=your-twitter-access-token
TWITTER_ACCESS_SECRET=your-twitter-access-token-secret
TWITTER_ADS_ACCOUNT_ID=your-twitter-ads-account-id

# TikTok Ads API (Short-form video ads)
# Get credentials: https://ads.tiktok.com/marketing_api/
TIKTOK_ACCESS_TOKEN=your-tiktok-marketing-api-access-token
TIKTOK_APP_ID=your-tiktok-app-id
TIKTOK_SECRET=your-tiktok-app-secret
TIKTOK_ADVERTISER_ID=your-tiktok-advertiser-id

# Pinterest Ads API (Visual discovery ads)
# Get your token: https://developers.pinterest.com/
PINTEREST_ACCESS_TOKEN=your-pinterest-access-token
PINTEREST_AD_ACCOUNT_ID=your-pinterest-ad-account-id

# Snapchat Ads API (Snapchat advertising)
# Get credentials: https://businesshelp.snapchat.com/
SNAPCHAT_CLIENT_ID=your-snapchat-client-id
SNAPCHAT_CLIENT_SECRET=your-snapchat-client-secret
SNAPCHAT_REFRESH_TOKEN=your-snapchat-refresh-token

# Microsoft/Bing Ads API (Search advertising)
# Get credentials: https://docs.microsoft.com/en-us/advertising/guides/
BING_ADS_CLIENT_ID=your-bing-ads-client-id
BING_ADS_CLIENT_SECRET=your-bing-ads-client-secret
BING_ADS_DEVELOPER_TOKEN=your-bing-ads-developer-token
BING_ADS_REFRESH_TOKEN=your-bing-ads-refresh-token
BING_ADS_CUSTOMER_ID=your-bing-ads-customer-id

# Google Tag Manager (Analytics & tracking)
# Get credentials: https://tagmanager.google.com/
GOOGLE_TAG_MANAGER_ID=GTM-XXXXXXX
GOOGLE_TAG_MANAGER_AUTH=your-gtm-auth-token

# Branch.io (Deep linking & attribution)
# Get your key: https://dashboard.branch.io/
BRANCH_KEY=key_live_your-branch-key

# AppsFlyer (Mobile attribution)
# Get your key: https://support.appsflyer.com/
APPSFLYER_DEV_KEY=your-appsflyer-dev-key

# ============================================================================
# PAYMENT & ECOMMERCE (If applicable)
# ============================================================================

# Stripe (Payment processing)
# Get your keys: https://dashboard.stripe.com/apikeys
STRIPE_SECRET_KEY=sk_live_your-stripe-secret-key
STRIPE_PUBLIC_KEY=pk_live_your-stripe-publishable-key
STRIPE_WEBHOOK_SECRET=whsec_your-stripe-webhook-secret

# PayPal (Alternative payment)
# Get credentials: https://developer.paypal.com/
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_CLIENT_SECRET=your-paypal-client-secret
PAYPAL_MODE=live

# Shopify (E-commerce platform)
# Get credentials: https://shopify.dev/api/admin-rest
SHOPIFY_API_KEY=your-shopify-api-key
SHOPIFY_API_SECRET=your-shopify-api-secret
SHOPIFY_STORE_DOMAIN=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=your-shopify-access-token

# ============================================================================
# DATABASE & STORAGE (If using external services)
# ============================================================================

# PostgreSQL (Production database)
DATABASE_URL=postgresql://username:password@host:port/database_name

# MongoDB (NoSQL alternative)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database

# Redis (Caching & sessions)
REDIS_URL=redis://username:password@host:port/0

# ============================================================================
# MONITORING & ERROR TRACKING
# ============================================================================

# Sentry (Error tracking)
# Get your DSN: https://sentry.io/settings/
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Datadog (Application monitoring)
# Get your key: https://app.datadoghq.com/
DATADOG_API_KEY=your-datadog-api-key
DATADOG_APP_KEY=your-datadog-application-key

# New Relic (Performance monitoring)
# Get your key: https://one.newrelic.com/
NEW_RELIC_LICENSE_KEY=your-new-relic-license-key

# LogDNA/Mezmo (Log management)
LOGDNA_INGESTION_KEY=your-logdna-ingestion-key

# ============================================================================
# APPLICATION SETTINGS
# ============================================================================

# Budget & Business Settings
MAX_BUDGET=100000
DEFAULT_BUDGET=5000
DEFAULT_TIMELINE_DAYS=90

# Performance Settings
DEFAULT_TIMEOUT=300
AGENT_TIMEOUT_SECONDS=300
MAX_CONCURRENT_AGENTS=6

# Feature Flags
ENABLE_METRICS=True
ENABLE_ASYNC_AGENTS=False
ENABLE_CACHING=True

# Logging
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30

# Security
SESSION_TIMEOUT_MINUTES=30
RATE_LIMIT=100 per minute

# ============================================================================
# NOTES:
# - Never commit this file to version control
# - After editing, encrypt with: python3 tools/encrypted_env_demo.py encrypt
# - Store .env.key in secure password manager or secrets vault
# - Not all APIs are required - only add what your agents will actually use
# - Free tiers are available for most services during development
# ============================================================================
"""

    def encrypt(self) -> bool:
        """
        Encrypt the .env file

        Returns:
            Success status
        """
        if not self.key_file.exists():
            print(f"❌ Encryption key not found. Run setup first:")
            print(f"   python3 tools/encrypted_env_demo.py setup")
            return False

        if not self.env_file.exists():
            print(f"❌ .env file not found at {self.env_file}")
            return False

        # Load encryption key
        key = self.key_file.read_bytes()
        fernet = Fernet(key)

        # Read and encrypt .env content
        env_content = self.env_file.read_bytes()
        encrypted_content = fernet.encrypt(env_content)

        # Save encrypted file
        self.encrypted_file.write_bytes(encrypted_content)
        print(f"✓ Encrypted {self.env_file} → {self.encrypted_file}")
        print(f"  Size: {len(env_content)} bytes → {len(encrypted_content)} bytes")
        print(f"\n📋 Safe to commit: {self.encrypted_file}")

        return True

    def decrypt(self, output_path: Optional[Path] = None) -> bool:
        """
        Decrypt the .env.encrypted file

        Args:
            output_path: Output path (defaults to .env)

        Returns:
            Success status
        """
        if not self.key_file.exists():
            print(f"❌ Encryption key not found at {self.key_file}")
            print(f"   Retrieve the key from your secure storage and place it here")
            return False

        if not self.encrypted_file.exists():
            print(f"❌ Encrypted file not found at {self.encrypted_file}")
            return False

        output_path = output_path or self.env_file

        # Load encryption key
        key = self.key_file.read_bytes()
        fernet = Fernet(key)

        try:
            # Read and decrypt
            encrypted_content = self.encrypted_file.read_bytes()
            decrypted_content = fernet.decrypt(encrypted_content)

            # Save decrypted file
            output_path.write_bytes(decrypted_content)
            print(f"✓ Decrypted {self.encrypted_file} → {output_path}")
            print(f"  Environment variables are now available")

            return True
        except Exception as e:
            print(f"❌ Decryption failed: {e}")
            print(f"   Ensure you're using the correct encryption key")
            return False

    def load_env(self, decrypt_first: bool = True) -> Dict[str, str]:
        """
        Load environment variables from encrypted file

        Args:
            decrypt_first: Whether to decrypt before loading

        Returns:
            Dictionary of environment variables
        """
        if decrypt_first and self.encrypted_file.exists():
            self.decrypt()

        env_vars = {}

        if self.env_file.exists():
            content = self.env_file.read_text()
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
                    # Also set in os.environ for immediate use
                    os.environ[key.strip()] = value.strip()

        return env_vars

    def show_status(self):
        """Display current configuration status"""
        print("📊 Encrypted Environment Configuration Status")
        print("=" * 60)
        print(f"Project root: {self.project_root}")
        print(f"\nFiles:")
        print(
            f"  .env.key:       {'✓ EXISTS' if self.key_file.exists() else '✗ MISSING'} (DO NOT COMMIT)"
        )
        print(
            f"  .env:           {'✓ EXISTS' if self.env_file.exists() else '✗ MISSING'} (DO NOT COMMIT)"
        )
        print(
            f"  .env.encrypted: {'✓ EXISTS' if self.encrypted_file.exists() else '✗ MISSING'} (SAFE TO COMMIT)"
        )

        if self.env_file.exists():
            content = self.env_file.read_text()
            lines = [l for l in content.splitlines() if l.strip() and not l.startswith("#")]
            print(f"\nEnvironment variables: {len(lines)} configured")

        print(f"\n📋 Recommendations:")
        if not self.key_file.exists():
            print(f"   → Run 'setup' to generate encryption key")
        elif not self.encrypted_file.exists():
            print(f"   → Run 'encrypt' to create encrypted file")
        else:
            print(f"   ✓ Configuration is properly encrypted")


def main():
    """CLI entrypoint"""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nCommands:")
        print("  setup   - Initial setup (generate key, create sample .env)")
        print("  encrypt - Encrypt .env file")
        print("  decrypt - Decrypt .env.encrypted file")
        print("  show    - Show configuration status")
        sys.exit(1)

    command = sys.argv[1].lower()
    manager = EncryptedEnvManager()

    if command == "setup":
        overwrite = "--overwrite" in sys.argv
        manager.setup(overwrite=overwrite)
    elif command == "encrypt":
        manager.encrypt()
    elif command == "decrypt":
        manager.decrypt()
    elif command == "show":
        manager.show_status()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
