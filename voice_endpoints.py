"""
Voice WebSocket Endpoints for Flask App
Add these endpoints to app.py to enable voice functionality

Integration instructions:
1. Add imports at top of app.py
2. Add these endpoints to your existing Flask app
3. Initialize voice service
4. Frontend will connect to these WebSocket events
"""

import asyncio
import base64
from datetime import datetime
from typing import Dict, Any

from flask_socketio import emit
from services.voice_service import get_voice_service
from logger import get_logger

logger = get_logger(__name__)

# Initialize voice service
voice_service = get_voice_service()

# Track active voice sessions
active_voice_sessions: Dict[str, Any] = {}


# ========================================
# VOICE WEBSOCKET ENDPOINTS
# ========================================


@socketio.on("voice_start")
def handle_voice_start(data):
    """
    Initialize a voice session

    Client sends:
    {
        "language": "en-US"  # Optional, defaults to en-US
    }

    Server responds:
    {
        "session_id": "uuid",
        "status": "ready",
        "timestamp": "ISO-8601"
    }
    """
    try:
        session_id = str(uuid.uuid4())
        user_id = request.sid
        language = data.get("language", "en-US")

        # Initialize session
        active_voice_sessions[user_id] = {
            "session_id": session_id,
            "language": language,
            "start_time": datetime.now(),
            "audio_chunks": [],
            "transcripts": [],
            "mode": "voice",
        }

        logger.info(f"Voice session started: {session_id} for user {user_id}")

        emit(
            "voice_ready",
            {"session_id": session_id, "status": "ready", "timestamp": datetime.now().isoformat()},
        )

    except Exception as e:
        logger.error(f"Error starting voice session: {e}")
        emit("voice_error", {"error": str(e), "timestamp": datetime.now().isoformat()})


@socketio.on("audio_chunk")
def handle_audio_chunk(audio_data):
    """
    Receive audio chunk from client microphone

    Client sends:
    Binary WebSocket frame containing audio bytes (16-bit PCM @ 16kHz)

    Server processes and emits transcription events
    """
    try:
        user_id = request.sid
        session = active_voice_sessions.get(user_id)

        if not session:
            logger.warning(f"Received audio chunk for inactive session: {user_id}")
            return

        # Store audio chunk
        session["audio_chunks"].append(audio_data)

        # Process with voice service (async)
        # Note: For real-time STT, you'd send to streaming API here
        # This is a simplified version - see full implementation below

        logger.debug(f"Received audio chunk: {len(audio_data)} bytes from {user_id}")

    except Exception as e:
        logger.error(f"Error processing audio chunk: {e}")
        emit("voice_error", {"error": str(e)})


@socketio.on("audio_stream_start")
async def handle_audio_stream_start(data):
    """
    Start streaming audio to Google Speech-to-Text

    This initiates a real-time transcription session
    """
    try:
        user_id = request.sid
        session = active_voice_sessions.get(user_id)

        if not session:
            emit("voice_error", {"error": "No active voice session"})
            return

        session["streaming"] = True

        # Transcript callback
        async def on_transcript(session_id, result):
            """Called when transcription result is available"""
            transcript_data = {
                "type": "transcript",
                "text": result["text"],
                "is_final": result["is_final"],
                "confidence": result.get("confidence"),
                "timestamp": result["timestamp"],
            }

            # Store transcript
            session["transcripts"].append(transcript_data)

            # Send to client
            await socketio.emit("transcription", transcript_data, room=user_id)

            # If final, send to LangGraph for processing
            if result["is_final"]:
                await process_agent_query(result["text"], user_id, session)

        # Create audio stream generator
        async def audio_generator():
            """Generate audio chunks from session queue"""
            while session.get("streaming", False):
                if session["audio_chunks"]:
                    chunk = session["audio_chunks"].pop(0)
                    yield chunk
                else:
                    await asyncio.sleep(0.01)  # Wait for more audio

        # Start processing audio stream
        await voice_service.process_audio_stream(
            session_id=session["session_id"],
            audio_stream=audio_generator(),
            on_transcript=on_transcript,
        )

    except Exception as e:
        logger.error(f"Error starting audio stream: {e}")
        emit("voice_error", {"error": str(e)})


@socketio.on("audio_stream_stop")
def handle_audio_stream_stop():
    """Stop audio streaming"""
    try:
        user_id = request.sid
        session = active_voice_sessions.get(user_id)

        if session:
            session["streaming"] = False
            logger.info(f"Audio streaming stopped for session: {session['session_id']}")

    except Exception as e:
        logger.error(f"Error stopping audio stream: {e}")


@socketio.on("voice_stop")
def handle_voice_stop():
    """
    End voice session

    Server responds with session statistics
    """
    try:
        user_id = request.sid
        session = active_voice_sessions.get(user_id)

        if not session:
            return

        # Calculate session stats
        duration = (datetime.now() - session["start_time"]).total_seconds()

        stats = {
            "session_id": session["session_id"],
            "duration_seconds": duration,
            "transcript_count": len(session["transcripts"]),
            "audio_chunks_received": len(session["audio_chunks"]),
        }

        logger.info(f"Voice session ended: {session['session_id']}, duration: {duration:.1f}s")

        # Clean up
        del active_voice_sessions[user_id]

        emit("voice_stopped", stats)

    except Exception as e:
        logger.error(f"Error stopping voice session: {e}")


async def process_agent_query(text: str, user_id: str, session: Dict[str, Any]):
    """
    Process user query through LangGraph agents and generate voice response

    Args:
        text: Transcribed user query
        user_id: Socket.IO user identifier
        session: Voice session data
    """
    try:
        logger.info(f"Processing voice query: {text}")

        # Send typing indicator
        await socketio.emit("agent_thinking", {"status": "processing", "query": text}, room=user_id)

        # Execute LangGraph agent system
        # (This integrates with your existing graph_architecture)
        from graph_architecture.main_graph import execute_multi_agent_system

        result = await execute_multi_agent_system(
            objectives=[text],
            config={"voice_mode": True, "user_id": user_id, "session_id": session["session_id"]},
        )

        # Extract agent responses
        agent_responses = []

        # CEO summary
        if "ceo_summary" in result:
            agent_responses.append({"agent": "ceo", "text": result["ceo_summary"]})

        # CFO analysis
        if "cfo_analysis" in result:
            agent_responses.append(
                {"agent": "cfo", "text": result["cfo_analysis"].get("summary", "")}
            )

        # Engineer output
        if "engineer_output" in result:
            agent_responses.append(
                {"agent": "engineer", "text": result["engineer_output"].get("summary", "")}
            )

        # Researcher findings
        if "researcher_output" in result:
            agent_responses.append(
                {"agent": "researcher", "text": result["researcher_output"].get("summary", "")}
            )

        # Generate voice responses for each agent
        for response in agent_responses:
            agent_type = response["agent"]
            text = response["text"]

            # Skip empty responses
            if not text or not text.strip():
                continue

            # Generate speech audio
            audio_bytes = voice_service.generate_speech(
                text=text, agent_type=agent_type, audio_format="MP3"
            )

            # Send audio and text to client
            await socketio.emit(
                "agent_response",
                {
                    "agent": agent_type,
                    "text": text,
                    "audio": base64.b64encode(audio_bytes).decode("utf-8"),
                    "audio_format": "mp3",
                    "timestamp": datetime.now().isoformat(),
                },
                room=user_id,
            )

            logger.info(
                f"Sent voice response from {agent_type}: {len(text)} chars, {len(audio_bytes)} bytes"
            )

    except Exception as e:
        logger.error(f"Error processing agent query: {e}", exc_info=True)
        await socketio.emit(
            "voice_error", {"error": f"Agent processing error: {str(e)}"}, room=user_id
        )


@socketio.on("request_voice_stats")
def handle_voice_stats_request():
    """Get current voice session statistics"""
    try:
        user_id = request.sid
        session = active_voice_sessions.get(user_id)

        if not session:
            emit("voice_stats", {"error": "No active session"})
            return

        stats = voice_service.get_session_stats(session["session_id"])
        emit("voice_stats", stats or {"error": "Session not found"})

    except Exception as e:
        logger.error(f"Error getting voice stats: {e}")
        emit("voice_error", {"error": str(e)})


# ========================================
# INTEGRATION INSTRUCTIONS
# ========================================

"""
To integrate into app.py:

1. Add imports:
   from services.voice_service import get_voice_service

2. Initialize voice service (after socketio creation):
   voice_service = get_voice_service()
   active_voice_sessions = {}

3. Copy all @socketio.on() decorated functions above

4. Ensure Google Cloud credentials are set:
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

   Or use gcloud CLI:
   gcloud auth application-default login

5. Install dependencies:
   pip install google-cloud-speech google-cloud-texttospeech pydub numpy

6. Frontend integration:
   - See static/js/voice-interface.js (created next)
   - Add voice toggle button to dashboard
   - Handle voice_ready, transcription, agent_response events

7. Test voice session:
   - Start session: socket.emit('voice_start', {})
   - Send audio: socket.emit('audio_chunk', binaryAudioData)
   - Receive transcripts: socket.on('transcription', callback)
   - Receive responses: socket.on('agent_response', callback)
"""
