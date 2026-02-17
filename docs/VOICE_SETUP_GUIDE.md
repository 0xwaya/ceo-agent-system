# 🎤 Voice Integration Setup Guide

**Status**: Ready for integration
**Phase**: 1 - Voice Service Backend
**Timeline**: Week 1-2

---

## ✅ What's Been Created

### 1. Voice Service Layer
- **File**: `services/voice_service.py`
- **Features**:
  - Google Cloud Speech-to-Text (streaming)
  - Google Cloud Text-to-Speech (Neural2 voices)
  - Voice Activity Detection (VAD)
  - Per-agent voice personalities (CEO, CFO, Engineer, Researcher)
  - Session management

### 2. WebSocket Endpoints
- **File**: `voice_endpoints.py`
- **Endpoints**:
  - `voice_start` - Initialize voice session
  - `audio_chunk` - Receive microphone audio
  - `audio_stream_start` - Start real-time STT
  - `audio_stream_stop` - Stop streaming
  - `voice_stop` - End session
  - `request_voice_stats` - Get session statistics

### 3. Frontend Voice Interface
- **File**: `static/js/voice-interface.js`
- **Features**:
  - VoiceInterface class
  - Microphone capture (Web Audio API)
  - Audio playback (MP3/PCM)
  - Transcription display
  - Voice UI controls

### 4. Audio Worklet Processors
- **File**: `static/js/pcm-recorder-processor.js` - Microphone capture
- **File**: `static/js/pcm-player-processor.js` - Audio playback

---

## 🚀 Integration Steps

### Step 1: Install Dependencies

```bash
cd /Users/pc/code/langraph
source .venv/bin/activate

# Install Google Cloud Speech APIs
pip install google-cloud-speech==2.21.0
pip install google-cloud-texttospeech==2.14.1

# Install audio processing libraries
pip install pydub==0.25.1
pip install numpy==1.24.3

# Update requirements.txt
pip freeze > requirements.txt
```

### Step 2: Set up Google Cloud Credentials

**Option A: Service Account (Recommended for production)**
```bash
# 1. Go to Google Cloud Console
# 2. Create a project (or use existing)
# 3. Enable APIs:
#    - Cloud Speech-to-Text API
#    - Cloud Text-to-Speech API
# 4. Create service account
# 5. Download JSON key file
# 6. Set environment variable

export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/key.json"

# Add to your .env file
echo 'GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/key.json"' >> .env
```

**Option B: gcloud CLI (For development)**
```bash
# Install gcloud CLI (if not installed)
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth application-default login

# Set project
gcloud config set project YOUR_PROJECT_ID
```

### Step 3: Update app.py

Add voice imports and endpoints to your existing `app.py`:

```python
# Add at top of app.py (with other imports)
from services.voice_service import get_voice_service
import uuid

# Initialize voice service (after socketio creation)
voice_service = get_voice_service()
active_voice_sessions = {}

# Copy WebSocket endpoints from voice_endpoints.py
# (All @socketio.on() decorated functions)
```

**Quick integration snippet:**
```python
# In app.py, add this section after existing Socket.IO endpoints

# ========================================
# VOICE WEBSOCKET ENDPOINTS
# ========================================

@socketio.on('voice_start')
def handle_voice_start(data):
    try:
        session_id = str(uuid.uuid4())
        user_id = request.sid
        language = data.get('language', 'en-US')

        active_voice_sessions[user_id] = {
            'session_id': session_id,
            'language': language,
            'start_time': datetime.now(),
            'audio_chunks': [],
            'transcripts': [],
            'mode': 'voice'
        }

        logger.info(f"Voice session started: {session_id}")

        emit('voice_ready', {
            'session_id': session_id,
            'status': 'ready',
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error starting voice session: {e}")
        emit('voice_error', {'error': str(e)})

# ... (add remaining endpoints from voice_endpoints.py)
```

### Step 4: Update Dashboard HTML

Add voice UI to `templates/graph_dashboard.html`:

```html
<!-- Add after existing header -->
<div class="voice-controls">
    <button id="voice-toggle-btn" class="btn btn-voice">
        <i class="fas fa-microphone"></i> Start Voice
    </button>
    <div id="voice-status" class="voice-status voice-status-disconnected">
        Voice inactive
    </div>
</div>

<!-- Add transcript panel -->
<div class="voice-panel">
    <h3>Voice Conversation</h3>
    <div id="voice-transcript" class="voice-transcript">
        <!-- Transcripts appear here -->
    </div>
</div>
```

### Step 5: Add Voice CSS

Add to `static/css/dark-theme.css`:

```css
/* Voice Controls */
.voice-controls {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background: var(--bg-secondary);
    border-radius: var(--radius);
    margin-bottom: 1rem;
}

.btn-voice {
    padding: 0.75rem 1.5rem;
    background: var(--accent-blue);
    color: white;
    border: none;
    border-radius: var(--radius);
    cursor: pointer;
    font-size: 1rem;
    transition: all 0.2s;
}

.btn-voice:hover {
    background: var(--accent-blue-hover);
}

.btn-voice.active {
    background: var(--error);
    animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

/* Voice Status */
.voice-status {
    padding: 0.5rem 1rem;
    border-radius: var(--radius);
    font-size: 0.9rem;
    font-weight: 500;
}

.voice-status-disconnected {
    background: var(--bg-secondary);
    color: var(--text-secondary);
}

.voice-status-connecting {
    background: var(--warning);
    color: var(--text-primary);
}

.voice-status-connected {
    background: var(--success);
    color: white;
}

.voice-status-listening {
    background: var(--accent-blue);
    color: white;
    animation: pulse 1s ease-in-out infinite;
}

.voice-status-processing {
    background: var(--warning);
    color: var(--text-primary);
}

.voice-status-error {
    background: var(--error);
    color: white;
}

/* Voice Transcript Panel */
.voice-panel {
    background: var(--bg-secondary);
    border-radius: var(--radius);
    padding: 1.5rem;
    margin-bottom: 2rem;
}

.voice-transcript {
    max-height: 400px;
    overflow-y: auto;
    padding: 1rem;
    background: var(--bg-primary);
    border-radius: var(--radius);
}

.transcript-item {
    margin-bottom: 1rem;
    padding: 0.75rem;
    border-radius: var(--radius);
    animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.transcript-item.user {
    background: var(--accent-blue);
    color: white;
    margin-left: 0;
    margin-right: 20%;
}

.transcript-item.agent {
    background: var(--bg-tertiary);
    color: var(--text-primary);
    margin-left: 20%;
    margin-right: 0;
}

.transcript-item.agent-ceo {
    border-left: 4px solid var(--accent-purple);
}

.transcript-item.agent-cfo {
    border-left: 4px solid var(--accent-green);
}

.transcript-item.agent-engineer {
    border-left: 4px solid var(--accent-blue);
}

.transcript-item.agent-researcher {
    border-left: 4px solid var(--accent-yellow);
}

.transcript-label {
    font-weight: 600;
    display: block;
    margin-bottom: 0.25rem;
    font-size: 0.85rem;
    text-transform: uppercase;
}

.transcript-text {
    display: block;
    line-height: 1.5;
}

.transcript-confidence {
    font-size: 0.75rem;
    opacity: 0.7;
    margin-left: 0.5rem;
}
```

### Step 6: Initialize Voice in Dashboard JavaScript

Add to `static/js/dashboard.js` (or create new file):

```javascript
// Initialize voice interface when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Existing dashboard initialization...

    // Initialize voice interface
    if (typeof VoiceInterface !== 'undefined') {
        const voiceInterface = new VoiceInterface(socket);
        voiceInterface.initUI();

        console.log('[DASHBOARD] Voice interface initialized');
    } else {
        console.warn('[DASHBOARD] VoiceInterface not loaded');
    }
});
```

### Step 7: Update graph_dashboard.html Scripts

Add voice scripts before closing `</body>`:

```html
<!-- Voice Interface Scripts -->
<script src="{{ url_for('static', filename='js/voice-interface.js') }}"></script>
<script>
    // Voice interface will auto-initialize from dashboard.js
</script>
```

### Step 8: Test Voice Integration

**Start Flask app:**
```bash
python3 app.py
```

**Open browser console:**
```
http://127.0.0.1:5001/graph
```

**Test sequence:**
1. Click "Start Voice" button
2. Allow microphone permissions
3. Speak: "What is our current budget status?"
4. Watch transcription appear in real-time
5. Hear agent responses with different voices
6. See transcript history

**Check logs:**
```bash
# In terminal, watch for:
# [VOICE] Session ready: <uuid>
# [VOICE] Transcription: <text>
# [VOICE] Agent response: ceo/cfo/engineer
```

---

## 🔧 Troubleshooting

### Issue: "No module named 'google.cloud.speech'"
```bash
pip install google-cloud-speech google-cloud-texttospeech
```

### Issue: "GOOGLE_APPLICATION_CREDENTIALS not set"
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
# Or use: gcloud auth application-default login
```

### Issue: "Microphone not accessible"
- Must use HTTPS (or localhost for dev)
- Check browser permissions
- Try different browser (Chrome/Edge recommended)

### Issue: "No audio playback"
- Check browser audio permissions
- Verify outputAudioContext creation
- Check browser console for errors

### Issue: "High latency >1s"
- Check network connection
- Verify Google Cloud region (use closest)
- Enable enhanced models (costs more but faster)

---

## 📊 Next Steps

### Current Status: ✅ Phase 1 Complete
- Voice service created ✅
- WebSocket endpoints ready ✅
- Frontend interface built ✅
- Integration guide provided ✅

### Next Phase: Testing & Optimization

**Week 2 Tasks:**
1. Integrate endpoints into app.py
2. Add voice UI to dashboard
3. Test end-to-end voice flow
4. Measure latency (target <300ms)
5. Test multi-agent voice responses
6. Verify different agent voices work

**Week 3 Tasks:**
1. Add Voice Activity Detection
2. Implement silence detection
3. Optimize audio compression
4. Add error handling
5. Create fallback to text mode
6. Production deployment prep

---

## 💰 Cost Monitoring

**Set up billing alerts in Google Cloud Console:**
1. Go to Billing → Budgets & alerts
2. Create budget (e.g., $100/month)
3. Set alerts at 50%, 90%, 100%

**Monitor usage:**
```bash
# Check current month usage
gcloud billing accounts describe ACCOUNT_ID

# Check Speech-to-Text usage
gcloud alpha billing accounts describe ACCOUNT_ID --format="value(usage)"
```

**Cost optimization tips:**
- Use standard STT model instead of enhanced (50% cheaper)
- Implement silence detection (reduce unnecessary API calls)
- Cache common responses
- Consider local Whisper for STT (free, but slower)

---

## 📞 Support

If you encounter issues:
1. Check browser console for errors
2. Check Flask logs for backend errors
3. Verify Google Cloud API quotas
4. Test with simple "Hello" query first
5. Review [VOICE_INTEGRATION_ROADMAP.md](VOICE_INTEGRATION_ROADMAP.md)

**Ready to integrate?** Follow steps 1-8 above to enable voice in your LangGraph CEO Agent System!
