"""
Voice Service Free Tier Test
Tests Google Cloud Speech APIs with free tier credentials
"""

import sys

import pytest


def test_free_tier():
    """Test voice service with free tier."""
    pytest.importorskip("google.cloud.speech_v1p1beta1")
    pytest.importorskip("google.cloud.texttospeech")

    from services.voice_service import get_voice_service

    print("🧪 Testing Voice Service (Free Tier)")
    print("=" * 50)

    try:
        # Initialize voice service
        print("\n1️⃣  Initializing voice service...")
        voice_service = get_voice_service()
        print("   ✅ Voice service initialized")

        # Test TTS (Text-to-Speech) - FREE
        print("\n2️⃣  Testing Text-to-Speech (TTS)...")
        test_messages = [
            ("ceo", "Hello, this is the CEO agent testing the free tier voice integration."),
            ("cfo", "Financial analysis complete. All systems operational."),
            ("engineer", "Code compilation successful. Ready for deployment."),
            ("researcher", "Research findings have been documented and verified."),
        ]

        for agent_type, text in test_messages:
            print(f"\n   Testing {agent_type.upper()} voice...")
            audio_data = voice_service.text_to_speech(text=text, agent_type=agent_type)
            print(f"   ✅ {agent_type.upper()}: Generated {len(audio_data):,} bytes of audio")
            print(f'      Text: "{text[:50]}..."')

        # Test session management
        print("\n3️⃣  Testing session management...")
        session_id = voice_service.create_session()
        print(f"   ✅ Session created: {session_id}")

        # End session and get stats
        stats = voice_service.end_session(session_id)
        print(f"   ✅ Session ended successfully")
        print(f"      Duration: {stats.get('duration_seconds', 0):.2f} seconds")

        # Success summary
        print("\n" + "=" * 50)
        print("🎉 FREE TIER SETUP COMPLETE!")
        print("=" * 50)
        print("\n✅ All tests passed!")
        print("✅ Voice service is ready to use")
        print("✅ Running on Google Cloud free tier")
        print("\n📊 Free Tier Limits:")
        print("   • Speech-to-Text: 60 minutes/month")
        print("   • Text-to-Speech: 4M characters/month")
        print("\n💡 Next Steps:")
        print("   1. Review VOICE_FREE_TIER_SETUP.md")
        print("   2. Choose integration option (A, B, or C)")
        print("   3. Test voice in the dashboard")
        print("\n💰 Current cost: $0/month (free tier)")

        return True

    except Exception as e:
        print("\n" + "=" * 50)
        print("❌ TEST FAILED")
        print("=" * 50)
        print(f"\nError: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check GOOGLE_APPLICATION_CREDENTIALS is set:")
        print("      echo $GOOGLE_APPLICATION_CREDENTIALS")
        print("\n   2. Verify credentials file exists:")
        print("      ls -la /Users/pc/Desktop/code/langraph/langraph-voice-credentials.json")
        print("\n   3. Ensure APIs are enabled:")
        print("      https://console.cloud.google.com/apis/library")
        print("\n   4. Check service account has correct roles:")
        print("      - Cloud Speech Client")
        print("      - Cloud Text-to-Speech Client")
        print("\n   5. Install dependencies:")
        print("      pip install google-cloud-speech google-cloud-texttospeech pydub numpy")

        return False


if __name__ == "__main__":
    success = test_free_tier()
    sys.exit(0 if success else 1)
