# Voice Integration - Free Tier Setup Guide

## Google Cloud Free Tier (No Credit Card Initially)

### Free Tier Limits (Monthly)
- **Speech-to-Text**: 60 minutes/month free
- **Text-to-Speech**: 4 million characters/month free (Neural2 voices)
- **Storage**: 5GB free
- **Bandwidth**: 1GB free egress to North America

**Perfect for**: Development, testing, demos, low-volume usage (~120 voice conversations/month)

---

## Step 1: Create Google Cloud Account (Free Tier)

### Option A: Free Trial ($300 credit, 90 days)
```bash
# Visit: https://cloud.google.com/free
# Sign up with Google account
# Get $300 credit (no charges after trial unless you upgrade)
```

### Option B: Always Free Tier (No credit card)
```bash
# Visit: https://console.cloud.google.com
# Sign in with Google account
# Create project without billing
# Limited to free tier only
```

---

## Step 2: Enable APIs (Free)

```bash
# Go to: https://console.cloud.google.com/apis/library

# Enable these APIs (click "Enable" - no charges):
1. Cloud Speech-to-Text API
2. Cloud Text-to-Speech API
```

---

## Step 3: Create Service Account (Free)

```bash
# Navigate to: https://console.cloud.google.com/iam-admin/serviceaccounts

# Click "Create Service Account":
Name: langraph-voice-service
Description: Voice integration for LangGraph agents
Role: Add these roles:
  - Cloud Speech Client
  - Cloud Text-to-Speech Client

# Click "Create Key":
Key Type: JSON
Download: langraph-voice-credentials.json
```

**Save the JSON file to**: `/Users/pc/code/langraph/langraph-voice-credentials.json`

---

## Step 4: Install Dependencies (Free)

```bash
cd /Users/pc/code/langraph
source .venv/bin/activate

# Install required packages
pip install google-cloud-speech==2.21.0
pip install google-cloud-texttospeech==2.14.1
pip install pydub==0.25.1
pip install numpy==1.24.3
```

---

## Step 5: Set Environment Variable

```bash
# Add to your shell config (~/.zshrc or ~/.bashrc):
export GOOGLE_APPLICATION_CREDENTIALS="/Users/pc/code/langraph/langraph-voice-credentials.json"

# Or set temporarily for current session:
export GOOGLE_APPLICATION_CREDENTIALS="/Users/pc/code/langraph/langraph-voice-credentials.json"

# Reload shell config:
source ~/.zshrc
```

---

## Step 6: Test Voice Service (Free)

Create a test file to verify setup:

```python
# test_voice_free.py
from services.voice_service import get_voice_service

def test_free_tier():
    """Test voice service with free tier."""
    voice_service = get_voice_service()

    # Test TTS (Text-to-Speech) - FREE
    print("Testing Text-to-Speech...")
    audio_data = voice_service.text_to_speech(
        text="Hello, this is the CEO agent testing free tier voice.",
        agent_type="ceo"
    )
    print(f"✅ TTS Success! Generated {len(audio_data)} bytes of audio")

    # Test session
    print("\nTesting session management...")
    session_id = voice_service.create_session()
    print(f"✅ Session created: {session_id}")

    stats = voice_service.end_session(session_id)
    print(f"✅ Session ended. Stats: {stats}")

    print("\n🎉 Free tier setup is working!")

if __name__ == "__main__":
    test_free_tier()
```

Run the test:
```bash
python3 test_voice_free.py
```

---

## Step 7: Free Tier Usage Monitoring

### Track Your Free Tier Usage

```bash
# View usage dashboard:
# https://console.cloud.google.com/billing/reports

# Set up budget alerts (optional):
# https://console.cloud.google.com/billing/budgets
# Budget: $0.01 (Alert if you go over free tier)
```

### Stay Within Free Tier

**Speech-to-Text** (60 min/month free):
- ~120 conversations at 30 seconds each
- ~60 conversations at 1 minute each
- ~30 conversations at 2 minutes each

**Text-to-Speech** (4M chars/month free):
- ~8,000 agent responses at 500 characters each
- ~4,000 agent responses at 1,000 characters each

**Tip**: The free tier resets monthly, so usage resets on the 1st of each month.

---

## Step 8: Integrate into app.py (No Cost)

Now that you're set up with free tier, integrate the voice endpoints:

```bash
# The code is already created in voice_endpoints.py
# Just need to add it to app.py
```

I can help you with one of these options:

### Option A: Minimal Integration (Fastest)
- Add voice endpoints to existing `app.py`
- Keep current dashboard, add voice button
- **Time**: 10 minutes
- **Changes**: ~50 lines in app.py, ~30 lines in HTML

### Option B: Full Integration (Recommended)
- Complete voice UI with transcription display
- Status indicators, error handling
- Agent voice switching (CEO/CFO/Engineer/Researcher)
- **Time**: 30 minutes
- **Changes**: ~200 lines total

### Option C: I'll Do It (Automatic)
- I'll integrate everything for you
- Just review and test
- **Time**: 2 minutes
- **Result**: Complete voice system ready to test

---

## Free Tier Cost Monitor Script

```python
# monitor_free_tier.py
from google.cloud import speech_v1, texttospeech_v1
from datetime import datetime

def check_quotas():
    """Check free tier usage (requires billing API)."""
    print(f"📊 Free Tier Usage Report - {datetime.now().strftime('%Y-%m-%d')}")
    print("\n⚠️  Note: Enable Cloud Billing API to see detailed quotas")
    print("Visit: https://console.cloud.google.com/billing/reports")
    print("\nFree Tier Limits:")
    print("  • Speech-to-Text: 60 minutes/month")
    print("  • Text-to-Speech: 4M characters/month")
    print("\n✅ Staying within free tier = $0 charges!")

if __name__ == "__main__":
    check_quotas()
```

---

## What Happens After Free Tier

If you exceed free tier limits:

1. **With Free Trial ($300 credit)**:
    - Uses credit automatically
    - No charges until credit exhausted

2. **With Billing Disabled**:
   - API requests get throttled/rejected
   - Error message: "Quota exceeded"
   - Resets next month

3. **With Billing Enabled** (after trial):
   - Pay-as-you-go rates:
     - STT: $0.006/15 seconds ($1.44/hour)
     - TTS: $0.000016/character ($16/1M chars)

---

## Next Steps

Which integration option would you like?

**A) Minimal** - Quick voice button (10 min)
**B) Full** - Complete voice UI (30 min)
**C) Automatic** - I'll integrate everything (2 min)

Just tell me A, B, or C and I'll proceed!

---

## Free Tier Tips

✅ **Best Practices:**
- Test during development with free tier
- Monitor usage at console.cloud.google.com
- Set up $0.01 budget alert
- Use shorter responses to save TTS characters
- Cache common responses (future optimization)

✅ **Free Tier is Perfect For:**
- Learning and experimentation
- Small demos and presentations
- Personal projects
- Proof-of-concept development
- Testing new features

🎯 **Your current setup costs: $0/month** (within free tier limits)
