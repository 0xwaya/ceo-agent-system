# Voice Service - Google Cloud Speech Integration
# Integration with LangGraph CEO Agent System
# Provides real-time speech-to-text and text-to-speech capabilities

from typing import AsyncGenerator, Optional, Dict, Any
from datetime import datetime

from google.cloud import speech_v1p1beta1 as speech
from google.cloud import texttospeech
import numpy as np

from logger import get_logger

logger = get_logger(__name__)


class GoogleSpeechToText:
    """Real-time speech-to-text using Google Cloud Speech API"""

    def __init__(self, language_code: str = "en-US"):
        """
        Initialize Google Cloud Speech-to-Text client

        Args:
            language_code: Language code (e.g., "en-US", "es-ES", "fr-FR")
        """
        self.client = speech.SpeechClient()
        self.language_code = language_code
        logger.info(f"Initialized GoogleSpeechToText with language: {language_code}")

    def create_streaming_config(
        self,
        enable_automatic_punctuation: bool = True,
        enable_word_time_offsets: bool = False,
        profanity_filter: bool = False,
    ) -> speech.StreamingRecognitionConfig:
        """
        Create streaming recognition configuration

        Args:
            enable_automatic_punctuation: Add punctuation to transcription
            enable_word_time_offsets: Include word timestamps
            profanity_filter: Filter profanity

        Returns:
            StreamingRecognitionConfig object
        """
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=self.language_code,
            enable_automatic_punctuation=enable_automatic_punctuation,
            enable_word_time_offsets=enable_word_time_offsets,
            profanity_filter=profanity_filter,
            # Use enhanced model for better accuracy (costs more)
            use_enhanced=True,
            model="default",  # or "phone_call", "video", "command_and_search"
        )

        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True,  # Get partial results while speaking
            single_utterance=False,  # Continue listening after first utterance
        )

        return streaming_config

    async def transcribe_audio_stream(
        self, audio_stream: AsyncGenerator[bytes, None], interim_results: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Transcribe streaming audio to text

        Args:
            audio_stream: AsyncGenerator yielding audio chunks (16-bit PCM @ 16kHz)
            interim_results: Yield partial results while speaking

        Yields:
            Dict with transcription results:
            {
                'text': str,
                'is_final': bool,
                'confidence': float,
                'timestamp': str
            }
        """
        streaming_config = self.create_streaming_config()

        # Create request generator
        async def request_generator():
            # First request with configuration
            yield speech.StreamingRecognizeRequest(streaming_config=streaming_config)

            # Subsequent requests with audio data
            async for audio_chunk in audio_stream:
                yield speech.StreamingRecognizeRequest(audio_content=audio_chunk)

        try:
            # Start streaming recognition
            responses = self.client.streaming_recognize(
                config=streaming_config, requests=request_generator()
            )

            # Process responses
            for response in responses:
                if not response.results:
                    continue

                result = response.results[0]

                if not result.alternatives:
                    continue

                alternative = result.alternatives[0]

                yield {
                    "text": alternative.transcript,
                    "is_final": result.is_final,
                    "confidence": alternative.confidence if result.is_final else None,
                    "timestamp": datetime.now().isoformat(),
                }

                # Log final results
                if result.is_final:
                    logger.info(
                        "STT Final: %s (confidence: %.2f)",
                        alternative.transcript,
                        alternative.confidence,
                    )

        except Exception as e:
            logger.error(f"Speech-to-text error: {e}")
            raise


class GoogleTextToSpeech:
    """Text-to-speech using Google Cloud TTS API"""

    # Voice configurations for different agent personalities
    VOICE_PROFILES = {
        "ceo": {
            "name": "en-US-Neural2-J",  # Mature, authoritative male
            "speaking_rate": 1.0,
            "pitch": 0.0,
        },
        "cfo": {
            "name": "en-US-Neural2-D",  # Professional male
            "speaking_rate": 0.95,
            "pitch": -2.0,
        },
        "engineer": {
            "name": "en-US-Neural2-A",  # Clear, technical male
            "speaking_rate": 1.05,
            "pitch": 2.0,
        },
        "researcher": {
            "name": "en-US-Neural2-F",  # Analytical female
            "speaking_rate": 0.98,
            "pitch": 0.0,
        },
        "default": {
            "name": "en-US-Neural2-C",  # Neutral female
            "speaking_rate": 1.0,
            "pitch": 0.0,
        },
    }

    def __init__(self):
        """Initialize Google Cloud Text-to-Speech client"""
        self.client = texttospeech.TextToSpeechClient()
        logger.info("Initialized GoogleTextToSpeech")

    def synthesize_speech(
        self,
        text: str,
        agent_type: str = "default",
        language_code: str = "en-US",
        audio_encoding: str = "MP3",
    ) -> bytes:
        """
        Convert text to natural speech

        Args:
            text: Text to synthesize
            agent_type: Type of agent (ceo, cfo, engineer, researcher, default)
            language_code: Language code
            audio_encoding: Audio format (MP3, LINEAR16, OGG_OPUS)

        Returns:
            Audio bytes in specified format
        """
        # Get voice profile for agent type
        voice_profile = self.VOICE_PROFILES.get(agent_type, self.VOICE_PROFILES["default"])

        # Build synthesis input
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Configure voice
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code, name=voice_profile["name"]
        )

        # Map audio encoding string to enum
        encoding_map = {
            "MP3": texttospeech.AudioEncoding.MP3,
            "LINEAR16": texttospeech.AudioEncoding.LINEAR16,
            "OGG_OPUS": texttospeech.AudioEncoding.OGG_OPUS,
        }

        # Configure audio output
        audio_config = texttospeech.AudioConfig(
            audio_encoding=encoding_map[audio_encoding],
            speaking_rate=voice_profile["speaking_rate"],
            pitch=voice_profile["pitch"],
            sample_rate_hertz=24000 if audio_encoding == "LINEAR16" else None,
        )

        try:
            # Synthesize speech
            response = self.client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )

            logger.info(
                "TTS: Synthesized %d chars for %s (%d bytes)",
                len(text),
                agent_type,
                len(response.audio_content),
            )
            return response.audio_content

        except Exception as e:
            logger.error(f"Text-to-speech error: {e}")
            raise


class VoiceActivityDetector:
    """Simple Voice Activity Detection based on audio energy"""

    def __init__(self, threshold: float = 0.02, silence_duration_ms: int = 1500):
        """
        Initialize VAD

        Args:
            threshold: Energy threshold for voice detection (0.0-1.0)
            silence_duration_ms: Milliseconds of silence before marking end of speech
        """
        self.threshold = threshold
        self.silence_duration_ms = silence_duration_ms
        self.last_voice_time = None
        self.is_speaking = False

    def detect_voice(self, audio_chunk: bytes, sample_rate: int = 16000) -> Dict[str, Any]:
        """
        Detect if audio chunk contains voice

        Args:
            audio_chunk: Audio bytes (16-bit PCM)
            sample_rate: Sample rate in Hz

        Returns:
            Dict with VAD results:
            {
                'has_voice': bool,
                'energy': float,
                'is_speech_start': bool,
                'is_speech_end': bool
            }
        """
        # Convert bytes to numpy array
        audio_data = np.frombuffer(audio_chunk, dtype=np.int16)

        # Calculate RMS energy
        energy = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2)) / 32768.0

        has_voice = energy > self.threshold

        # Detect speech boundaries
        current_time = datetime.now()
        is_speech_start = False
        is_speech_end = False

        if has_voice:
            if not self.is_speaking:
                is_speech_start = True
                self.is_speaking = True
            self.last_voice_time = current_time
        else:
            if self.is_speaking and self.last_voice_time:
                silence_ms = (current_time - self.last_voice_time).total_seconds() * 1000
                if silence_ms > self.silence_duration_ms:
                    is_speech_end = True
                    self.is_speaking = False

        return {
            "has_voice": has_voice,
            "energy": float(energy),
            "is_speech_start": is_speech_start,
            "is_speech_end": is_speech_end,
        }


class VoiceService:
    """Unified voice service combining STT, TTS, and VAD"""

    def __init__(self, language_code: str = "en-US"):
        """
        Initialize voice service

        Args:
            language_code: Default language code
        """
        self.stt = GoogleSpeechToText(language_code=language_code)
        self.tts = GoogleTextToSpeech()
        self.vad = VoiceActivityDetector()
        self.active_sessions = {}
        logger.info(f"VoiceService initialized with language: {language_code}")

    async def process_audio_stream(
        self,
        session_id: str,
        audio_stream: AsyncGenerator[bytes, None],
        on_transcript: callable,
        enable_vad: bool = True,
    ) -> None:
        """
        Process audio stream with optional VAD

        Args:
            session_id: Unique session identifier
            audio_stream: AsyncGenerator yielding audio chunks
            on_transcript: Callback for transcription results
            enable_vad: Enable voice activity detection
        """
        self.active_sessions[session_id] = {
            "start_time": datetime.now(),
            "transcript_count": 0,
        }

        try:
            async for result in self.stt.transcribe_audio_stream(audio_stream):
                # Call transcript callback
                await on_transcript(session_id, result)

                self.active_sessions[session_id]["transcript_count"] += 1

        except Exception as e:
            logger.error(f"Audio stream processing error for session {session_id}: {e}")
        finally:
            # Clean up session
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                duration = (datetime.now() - session["start_time"]).total_seconds()
                logger.info(
                    f"Session {session_id} ended. Duration: {duration:.1f}s, "
                    f"Transcripts: {session['transcript_count']}"
                )
                del self.active_sessions[session_id]

    def generate_speech(
        self, text: str, agent_type: str = "default", audio_format: str = "MP3"
    ) -> bytes:
        """
        Generate speech audio from text

        Args:
            text: Text to speak
            agent_type: Agent personality (ceo, cfo, engineer, researcher)
            audio_format: Audio format (MP3, LINEAR16, OGG_OPUS)

        Returns:
            Audio bytes
        """
        return self.tts.synthesize_speech(
            text=text, agent_type=agent_type, audio_encoding=audio_format
        )

    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for active session

        Args:
            session_id: Session identifier

        Returns:
            Session stats or None if session not found
        """
        if session_id not in self.active_sessions:
            return None

        session = self.active_sessions[session_id]
        duration = (datetime.now() - session["start_time"]).total_seconds()

        return {
            "session_id": session_id,
            "duration_seconds": duration,
            "transcript_count": session["transcript_count"],
            "start_time": session["start_time"].isoformat(),
        }


# Singleton instance
_voice_service_instance = None


def get_voice_service() -> VoiceService:
    """Get singleton VoiceService instance"""
    global _voice_service_instance
    if _voice_service_instance is None:
        _voice_service_instance = VoiceService()
    return _voice_service_instance
