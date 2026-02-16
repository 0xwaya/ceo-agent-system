/**
 * Voice Interface for LangGraph CEO Agent System
 * Handles browser-based voice input/output with Web Audio API
 *
 * Features:
 * - Microphone capture (16-bit PCM @ 16kHz)
 * - Real-time audio streaming via WebSocket
 * - Speech-to-text transcription display
 * - Text-to-speech audio playback
 * - Voice Activity Detection (optional)
 *
 * Usage:
 * const voiceInterface = new VoiceInterface(socket);
 * await voiceInterface.startVoice();
 */

class VoiceInterface {
    constructor(socket) {
        this.socket = socket;
        this.isRecording = false;
        this.isPlaying = false;

        // Audio contexts
        this.inputAudioContext = null;
        this.outputAudioContext = null;

        // Audio nodes
        this.micStream = null;
        this.audioRecorderNode = null;
        this.audioPlayerNode = null;

        // Session info
        this.sessionId = null;
        this.transcripts = [];

        // UI elements (will be set by initUI)
        this.voiceButton = null;
        this.transcriptDisplay = null;
        this.statusIndicator = null;

        this.setupEventListeners();
    }

    /**
     * Initialize UI elements
     */
    initUI() {
        // Voice toggle button
        this.voiceButton = document.getElementById('voice-toggle-btn');
        if (!this.voiceButton) {
            console.error('Voice toggle button not found');
            return;
        }

        this.voiceButton.addEventListener('click', () => {
            if (!this.isRecording) {
                this.startVoice();
            } else {
                this.stopVoice();
            }
        });

        // Transcript display area
        this.transcriptDisplay = document.getElementById('voice-transcript');

        // Status indicator
        this.statusIndicator = document.getElementById('voice-status');
    }

    /**
     * Set up WebSocket event listeners
     */
    setupEventListeners() {
        // Voice session ready
        this.socket.on('voice_ready', (data) => {
            console.log('[VOICE] Session ready:', data);
            this.sessionId = data.session_id;
            this.updateStatus('connected', 'Voice session active');
        });

        // Transcription received
        this.socket.on('transcription', (data) => {
            console.log('[VOICE] Transcription:', data);
            this.handleTranscription(data);
        });

        // Agent response with audio
        this.socket.on('agent_response', (data) => {
            console.log('[VOICE] Agent response:', data.agent, data.text.substring(0, 50) + '...');
            this.handleAgentResponse(data);
        });

        // Agent thinking indicator
        this.socket.on('agent_thinking', (data) => {
            console.log('[VOICE] Agent processing:', data.query);
            this.updateStatus('processing', 'Agent is thinking...');
        });

        // Voice stopped
        this.socket.on('voice_stopped', (stats) => {
            console.log('[VOICE] Session ended:', stats);
            this.updateStatus('disconnected', 'Voice session ended');
        });

        // Voice error
        this.socket.on('voice_error', (data) => {
            console.error('[VOICE] Error:', data.error);
            this.updateStatus('error', `Error: ${data.error}`);
            alert(`Voice error: ${data.error}`);
        });
    }

    /**
     * Start voice session
     */
    async startVoice() {
        try {
            console.log('[VOICE] Starting voice session...');
            this.updateStatus('connecting', 'Starting voice...');

            // Request microphone permissions
            await this.initMicrophone();

            // Initialize audio player
            await this.initAudioPlayer();

            // Start voice session on server
            this.socket.emit('voice_start', {
                language: 'en-US'
            });

            // Start audio streaming
            this.socket.emit('audio_stream_start', {});

            this.isRecording = true;
            this.updateVoiceButton(true);

            console.log('[VOICE] Voice session started');

        } catch (error) {
            console.error('[VOICE] Failed to start voice:', error);
            this.updateStatus('error', `Failed to start: ${error.message}`);
            alert(`Could not start voice: ${error.message}`);
        }
    }

    /**
     * Stop voice session
     */
    async stopVoice() {
        try {
            console.log('[VOICE] Stopping voice session...');

            // Stop audio streaming
            this.socket.emit('audio_stream_stop', {});

            // Stop microphone
            if (this.micStream) {
                this.micStream.getTracks().forEach(track => track.stop());
                this.micStream = null;
            }

            // Close audio contexts
            if (this.inputAudioContext && this.inputAudioContext.state !== 'closed') {
                await this.inputAudioContext.close();
                this.inputAudioContext = null;
            }

            if (this.outputAudioContext && this.outputAudioContext.state !== 'closed') {
                await this.outputAudioContext.close();
                this.outputAudioContext = null;
            }

            // Stop voice session on server
            this.socket.emit('voice_stop', {});

            this.isRecording = false;
            this.updateVoiceButton(false);
            this.updateStatus('disconnected', 'Voice stopped');

            console.log('[VOICE] Voice session stopped');

        } catch (error) {
            console.error('[VOICE] Error stopping voice:', error);
        }
    }

    /**
     * Initialize microphone capture
     */
    async initMicrophone() {
        // Request microphone with specific constraints
        this.micStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,          // Mono
                sampleRate: 16000,        // 16kHz (required by Google Speech API)
                echoCancellation: true,   // Reduce echo
                noiseSuppression: true,   // Reduce background noise
                autoGainControl: true     // Normalize volume
            }
        });

        // Create audio context with 16kHz sample rate
        this.inputAudioContext = new AudioContext({ sampleRate: 16000 });

        // Load audio recorder worklet
        await this.inputAudioContext.audioWorklet.addModule('/static/js/pcm-recorder-processor.js');

        // Create audio recorder node
        this.audioRecorderNode = new AudioWorkletNode(
            this.inputAudioContext,
            'pcm-recorder-processor'
        );

        // Connect microphone to recorder
        const source = this.inputAudioContext.createMediaStreamSource(this.micStream);
        source.connect(this.audioRecorderNode);

        // Handle audio data from worklet
        this.audioRecorderNode.port.onmessage = (event) => {
            const pcmData = this.convertFloat32ToPCM(event.data);

            // Send binary audio to server
            if (this.socket && this.isRecording) {
                this.socket.emit('audio_chunk', pcmData);
            }
        };

        console.log('[VOICE] Microphone initialized');
    }

    /**
     * Initialize audio player for TTS output
     */
    async initAudioPlayer() {
        // Create audio context for playback (24kHz for high quality)
        this.outputAudioContext = new AudioContext({ sampleRate: 24000 });

        // Load audio player worklet
        await this.outputAudioContext.audioWorklet.addModule('/static/js/pcm-player-processor.js');

        // Create audio player node
        this.audioPlayerNode = new AudioWorkletNode(
            this.outputAudioContext,
            'pcm-player-processor'
        );

        // Connect to speakers
        this.audioPlayerNode.connect(this.outputAudioContext.destination);

        console.log('[VOICE] Audio player initialized');
    }

    /**
     * Convert Float32Array to 16-bit PCM
     */
    convertFloat32ToPCM(float32Array) {
        const pcm16 = new Int16Array(float32Array.length);
        for (let i = 0; i < float32Array.length; i++) {
            // Clamp to [-1.0, 1.0] and convert to 16-bit
            const s = Math.max(-1, Math.min(1, float32Array[i]));
            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return pcm16.buffer;  // Return ArrayBuffer
    }

    /**
     * Handle transcription from server
     */
    handleTranscription(data) {
        const { text, is_final, confidence } = data;

        if (!this.transcriptDisplay) return;

        if (is_final) {
            // Final transcription - add to history
            this.transcripts.push(text);

            const transcriptElement = document.createElement('div');
            transcriptElement.className = 'transcript-item user';
            transcriptElement.innerHTML = `
                <span class="transcript-label">You:</span>
                <span class="transcript-text">${text}</span>
                ${confidence ? `<span class="transcript-confidence">(${(confidence * 100).toFixed(0)}%)</span>` : ''}
            `;
            this.transcriptDisplay.appendChild(transcriptElement);

            // Auto-scroll to bottom
            this.transcriptDisplay.scrollTop = this.transcriptDisplay.scrollHeight;
        } else {
            // Interim transcription - show in status
            this.updateStatus('listening', `Listening: "${text}"`);
        }
    }

    /**
     * Handle agent response with audio
     */
    async handleAgentResponse(data) {
        const { agent, text, audio, audio_format } = data;

        // Display text transcript
        if (this.transcriptDisplay) {
            const transcriptElement = document.createElement('div');
            transcriptElement.className = `transcript-item agent agent-${agent}`;
            transcriptElement.innerHTML = `
                <span class="transcript-label">${agent.toUpperCase()}:</span>
                <span class="transcript-text">${text}</span>
            `;
            this.transcriptDisplay.appendChild(transcriptElement);

            // Auto-scroll
            this.transcriptDisplay.scrollTop = this.transcriptDisplay.scrollHeight;
        }

        // Play audio response
        if (audio && this.audioPlayerNode) {
            await this.playAudio(audio, audio_format);
        }

        this.updateStatus('connected', 'Listening...');
    }

    /**
     * Play audio from base64 string
     */
    async playAudio(base64Audio, format) {
        try {
            // Decode base64 to ArrayBuffer
            const binaryString = atob(base64Audio);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }

            if (format === 'mp3') {
                // Decode MP3 using Web Audio API
                const audioBuffer = await this.outputAudioContext.decodeAudioData(bytes.buffer);

                // Create buffer source
                const source = this.outputAudioContext.createBufferSource();
                source.buffer = audioBuffer;
                source.connect(this.outputAudioContext.destination);

                // Play
                source.start(0);

                console.log('[VOICE] Playing MP3 audio:', audioBuffer.duration.toFixed(2), 'seconds');

            } else if (format === 'pcm') {
                // Send PCM directly to player worklet
                this.audioPlayerNode.port.postMessage(bytes.buffer);

                console.log('[VOICE] Playing PCM audio:', bytes.length, 'bytes');
            }

        } catch (error) {
            console.error('[VOICE] Error playing audio:', error);
        }
    }

    /**
     * Update status indicator
     */
    updateStatus(state, message) {
        if (!this.statusIndicator) return;

        this.statusIndicator.className = `voice-status voice-status-${state}`;
        this.statusIndicator.textContent = message;

        console.log(`[VOICE] Status: ${state} - ${message}`);
    }

    /**
     * Update voice button appearance
     */
    updateVoiceButton(isActive) {
        if (!this.voiceButton) return;

        if (isActive) {
            this.voiceButton.classList.add('active');
            this.voiceButton.innerHTML = '<i class="fas fa-microphone-slash"></i> Stop Voice';
        } else {
            this.voiceButton.classList.remove('active');
            this.voiceButton.innerHTML = '<i class="fas fa-microphone"></i> Start Voice';
        }
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoiceInterface;
}
