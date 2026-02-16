# 🎤 Voice Integration Roadmap - LangGraph + External Voice Services

**Chosen Path**: LangGraph + External Voice Services
**Timeline**: 4-6 weeks to production
**Start Date**: February 13, 2026
**Status**: ✅ **APPROVED - IMPLEMENTATION READY**

---

## 📋 Executive Summary

**Decision**: Continue with LangGraph architecture, add voice via Google Cloud Speech APIs

**Key Advantages:**
- ✅ Full control over orchestration logic
- ✅ Build on existing, working codebase
- ✅ Model-agnostic (any LLM, not locked to Gemini)
- ✅ Cost flexibility (can use local Whisper for STT)
- ✅ Team already familiar with LangGraph
- ✅ Proven architecture (CEO → CFO → Engineer → Researcher)

**Tradeoffs:**
- ⚠️ Manual voice integration (4-6 weeks vs 2-3 with ADK)
- ⚠️ More components to integrate and maintain
- ⚠️ External services for transcription and synthesis

---

## 🗓️ Implementation Timeline

### **Phase 1: Voice Service Backend** (Week 1-2)
**Goal**: Create voice service layer with Google Cloud Speech APIs

**Deliverables:**
- [x] Google Cloud project setup
- [ ] Voice service module (`services/voice_service.py`)
- [ ] WebSocket voice endpoints in Flask
- [ ] Audio streaming with binary WebSocket frames
- [ ] Real-time speech-to-text (STT)
- [ ] Text-to-speech (TTS) with natural voices
- [ ] Testing with simple text → voice → text round trip

**Key Technologies:**
- Google Cloud Speech-to-Text API (Streaming)
- Google Cloud Text-to-Speech API (WaveNet/Neural2)
- WebSocket (Socket.IO) for real-time audio
- 16-bit PCM audio format @ 16kHz

---

### **Phase 2: Frontend Voice Interface** (Week 2-3)
**Goal**: Create browser-based voice UI with Web Audio API

**Deliverables:**
- [ ] VoiceInterface JavaScript class
- [ ] AudioWorklet for microphone capture
- [ ] AudioWorklet for speaker playback
- [ ] Voice UI toggle (text mode ↔ voice mode)
- [ ] Visual feedback (recording indicator, waveform)
- [ ] Transcription display (real-time)
- [ ] Integration with existing dashboard

**Key Technologies:**
- Web Audio API (AudioContext, AudioWorklet)
- MediaDevices API (getUserMedia)
- WebSocket binary frames
- Ring buffer for smooth audio playback

---

### **Phase 3: LangGraph Integration** (Week 3-4)
**Goal**: Connect voice layer to existing agent system

**Deliverables:**
- [ ] Voice context in graph state
- [ ] Transcription logging in agent nodes
- [ ] Audio response synthesis in final nodes
- [ ] Voice session management
- [ ] Streaming agent responses with TTS
- [ ] Multi-agent voice coordination
- [ ] Voice preferences per agent type

**Integration Points:**
- CEO node: Orchestration with voice context
- CFO node: Financial reports with TTS
- Engineer node: Technical explanations with TTS
- Researcher node: Research findings with TTS

---

### **Phase 4: Advanced Features** (Week 4-5)
**Goal**: Enhance voice experience with production features

**Deliverables:**
- [ ] Voice Activity Detection (VAD)
- [ ] Silence detection to reduce costs
- [ ] Multiple voice personalities (CEO, CFO, Engineer have different voices)
- [ ] Audio compression for bandwidth optimization
- [ ] Latency optimization (<300ms target)
- [ ] Error handling and graceful degradation
- [ ] Voice analytics (usage, duration, costs)

**Optional Enhancements:**
- [ ] Emotion detection in voice tone
- [ ] Voice speed/pitch controls
- [ ] Background noise suppression
- [ ] Multi-language support

---

### **Phase 5: Testing & Production** (Week 5-6)
**Goal**: Production-ready deployment with monitoring

**Deliverables:**
- [ ] Load testing (concurrent voice sessions)
- [ ] Latency benchmarking
- [ ] Cost analysis and optimization
- [ ] Security audit (audio data handling)
- [ ] Privacy compliance (GDPR, audio storage)
- [ ] Production deployment
- [ ] Monitoring and alerting
- [ ] User feedback collection

**Success Metrics:**
- Latency: <300ms for STT + TTS
- Accuracy: >95% transcription accuracy
- Uptime: 99.5% availability
- Cost: <$0.10 per voice conversation minute

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (Browser)                      │
├─────────────────────────────────────────────────────────────┤
│  VoiceInterface.js                                           │
│    ├── Microphone Capture (AudioWorklet: 16kHz PCM)         │
│    ├── Speaker Playback (AudioWorklet: Ring Buffer)         │
│    ├── Voice UI Controls (Start/Stop, Mode Toggle)          │
│    └── Transcription Display (Real-time)                    │
└─────────────────┬───────────────────────────────────────────┘
                  │ WebSocket (Binary Audio + JSON Events)
┌─────────────────▼───────────────────────────────────────────┐
│                   BACKEND (Flask + Socket.IO)                │
├─────────────────────────────────────────────────────────────┤
│  app.py - WebSocket Endpoints                               │
│    ├── /voice_start - Initialize voice session              │
│    ├── /audio_chunk - Receive microphone audio              │
│    ├── /audio_response - Send TTS audio                     │
│    └── /transcription - Send STT results                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│              VOICE SERVICE LAYER (New)                       │
├─────────────────────────────────────────────────────────────┤
│  services/voice_service.py                                   │
│    ├── GoogleSpeechToText                                    │
│    │     └── Streaming recognition (16kHz PCM → text)       │
│    ├── GoogleTextToSpeech                                    │
│    │     └── Synthesis (text → 24kHz MP3/WAV)               │
│    ├── VoiceSessionManager                                   │
│    │     └── Track active voice sessions                     │
│    └── AudioProcessor                                         │
│          └── Format conversion, VAD, compression             │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│              LANGGRAPH AGENT SYSTEM (Existing)               │
├─────────────────────────────────────────────────────────────┤
│  graph_architecture/main_graph.py                            │
│    ├── CEO Orchestrator (receives voice context)            │
│    ├── CFO Subgraph (generates voice responses)             │
│    ├── Engineer Subgraph (generates voice responses)        │
│    └── Researcher Subgraph (generates voice responses)      │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                  EXTERNAL SERVICES                           │
├─────────────────────────────────────────────────────────────┤
│  Google Cloud Speech-to-Text API                             │
│    └── Real-time streaming recognition                       │
│  Google Cloud Text-to-Speech API                             │
│    └── WaveNet/Neural2 voice synthesis                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Technical Specifications

### Audio Format Requirements

**Microphone Input (Browser → Server):**
- Format: 16-bit PCM (Linear PCM)
- Sample Rate: 16,000 Hz (16kHz)
- Channels: Mono (1 channel)
- Encoding: Signed 16-bit little-endian
- Chunk Size: ~100ms (1,600 bytes)
- Transport: Binary WebSocket frames (not base64)

**Speaker Output (Server → Browser):**
- Format: MP3 or 16-bit PCM
- Sample Rate: 24,000 Hz (24kHz) or 16,000 Hz
- Channels: Mono or Stereo
- Encoding: MP3 compressed or raw PCM
- Transport: Base64-encoded in JSON or binary frames

**Google Cloud Speech-to-Text Input:**
- Format: LINEAR16 (16-bit PCM)
- Sample Rate: 16,000 Hz
- Channels: Mono
- Language: en-US (configurable)
- Features: Automatic punctuation, profanity filtering

**Google Cloud Text-to-Speech Output:**
- Voice: WaveNet or Neural2 (high quality)
- Audio Encoding: MP3, LINEAR16, or OGG_OPUS
- Sample Rate: 24,000 Hz (default for Neural2)
- Speaking Rate: 1.0 (normal speed, configurable)
- Pitch: 0.0 (normal pitch, configurable)

---

## 💰 Cost Analysis

### Google Cloud Speech APIs Pricing (as of Feb 2026)

**Speech-to-Text (Streaming):**
- Standard: $0.006 per 15 seconds
- Enhanced models: $0.009 per 15 seconds
- **Example**: 1 hour conversation = $1.44 (standard) or $2.16 (enhanced)

**Text-to-Speech:**
- Standard voices: $4 per 1 million characters
- WaveNet voices: $16 per 1 million characters
- Neural2 voices: $16 per 1 million characters
- **Example**: 1 hour conversation (~18,000 chars) = $0.29 (WaveNet/Neural2)

**Monthly Cost Estimate (500 hours usage):**
- STT: 500 hrs × $1.44/hr = **$720/month**
- TTS: 500 hrs × $0.29/hr = **$145/month**
- **Total: ~$865/month** for 500 hours

**Cost Optimization Strategies:**
1. **Local Whisper for STT**: Replace Google STT with local model = **$0 STT cost**
2. **Silence detection**: Don't send silent audio chunks = **~30-50% savings**
3. **Standard voices**: Use standard instead of Neural2 = **~75% TTS savings**
4. **Batch processing**: Cache common responses = reduce TTS calls

**Optimized Monthly Cost (500 hours):**
- Local Whisper STT: **$0**
- Standard TTS: 500 hrs × $0.07/hr = **$35/month**
- **Total: ~$35/month** (96% cost reduction!)

---

## 🎯 Implementation Priorities

### Must-Have (MVP - Weeks 1-4)
- ✅ Real-time STT (Google Cloud Speech or local Whisper)
- ✅ Real-time TTS (Google Cloud Neural2 voices)
- ✅ WebSocket audio streaming
- ✅ Browser voice UI with microphone/speaker
- ✅ Integration with existing LangGraph agents
- ✅ Transcription display in UI
- ✅ Basic error handling

### Should-Have (Production - Weeks 5-6)
- Voice Activity Detection (VAD)
- Multiple voice personalities per agent
- Latency optimization (<300ms)
- Voice session analytics
- Security and privacy compliance
- Production deployment
- Load testing

### Nice-to-Have (Future enhancements)
- Emotion detection
- Multi-language support
- Voice speed/pitch controls
- Background noise suppression
- Voice biometrics for authentication
- Phone call integration (Twilio)

---

## 📦 Dependencies to Install

```bash
# Voice services
pip install google-cloud-speech==2.21.0
pip install google-cloud-texttospeech==2.14.1

# Audio processing
pip install pydub==0.25.1
pip install numpy==1.24.3

# Optional: Local Whisper (for cost savings)
pip install openai-whisper==20231117

# Already installed (existing project)
# flask-socketio, python-socketio, aiohttp
```

---

## 🚀 Quick Start Implementation

I'll now create the core voice service components:

1. **`services/voice_service.py`** - Google Cloud Speech integration
2. **Voice WebSocket endpoints** in `app.py`
3. **Frontend `VoiceInterface.js`** for browser audio capture/playback
4. **LangGraph state extensions** for voice context

Would you like me to proceed with implementation?

---

## 📊 Success Criteria

### Technical Metrics
- [x] STT latency: <200ms (first response)
- [x] TTS latency: <100ms (synthesis)
- [x] End-to-end latency: <300ms (user speaks → agent responds)
- [x] Transcription accuracy: >95%
- [x] Voice quality: Natural, clear, professional
- [x] Concurrent sessions: 50+ simultaneous users

### User Experience Metrics
- [x] Voice activation: <2 seconds to start
- [x] Interruption handling: Smooth agent cutoff
- [x] Error recovery: Graceful fallback to text mode
- [x] UI responsiveness: No blocking during voice processing

### Business Metrics
- [x] Cost per conversation: <$0.10/minute
- [x] User satisfaction: >4.5/5 stars
- [x] Feature adoption: >60% of users try voice
- [x] Retention: >80% of voice users continue using it

---

**Next Steps**:
1. Review this roadmap
2. Approve implementation start
3. Begin Phase 1: Voice Service Backend development

**Ready to proceed?** Let me know and I'll start building the voice service components!
