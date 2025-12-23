"""
Main FastAPI application with Socket.io integration
This is the entry point for the backend server
"""
from datetime import datetime
import json
import base64
import aiohttp
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import socketio
from app.config import settings
from app.websocket.socket_manager import sio

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Socket.io
socket_app = socketio.ASGIApp(
    sio,
    other_asgi_app=app,
    socketio_path="/socket.io"
)

# Request models
class RunCodeRequest(BaseModel):
    session_id: str
    code: str
    problem_id: str

class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "en-US-JennyNeural"

class SessionConfigRequest(BaseModel):
    candidate_name: str
    experience_years: int
    target_role: str
    skills: Optional[str] = ""
    focus_area: Optional[str] = ""

class STTRequest(BaseModel):
    audio: str  # Base64 encoded audio

@app.post("/api/run_code")
async def run_code_api(request: RunCodeRequest):
    """Execute code via Judge0 (REST API)"""
    try:
        from app.services.judge0_service import Judge0Service
        judge = Judge0Service()
        result = await judge.execute_code(request.code, request.problem_id)
        return result
    except Exception as e:
        return {"status": "error", "stderr": str(e)}

@app.post("/api/tts")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech using Azure Speech Services.
    Returns audio as base64 encoded MP3.
    """
    try:
        from app.services.speech_service import get_speech_service
        
        speech_service = get_speech_service()
        audio_data = await speech_service.text_to_speech(request.text)
        
        if audio_data:
            # Return as base64 for easy frontend consumption
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            return {
                "success": True,
                "audio": audio_base64,
                "format": "mp3",
                "voice": request.voice
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate speech")
            
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")

@app.post("/api/tts/audio")
async def text_to_speech_audio(request: TTSRequest):
    """
    Convert text to speech and return raw audio bytes.
    Use this for direct audio playback.
    """
    try:
        from app.services.speech_service import get_speech_service
        
        speech_service = get_speech_service()
        audio_data = await speech_service.text_to_speech(request.text)
        
        if audio_data:
            return Response(
                content=audio_data,
                media_type="audio/mpeg",
                headers={"Content-Disposition": "inline; filename=speech.mp3"}
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to generate speech")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")

@app.post("/api/stt")
async def speech_to_text(request: STTRequest):
    """
    Convert audio to text using Azure Speech Services.
    Accepts base64 encoded audio (WAV or WebM).
    """
    try:
        import base64
        from app.services.speech_service import get_speech_service
        
        # Decode base64 audio
        audio_data = base64.b64decode(request.audio)
        
        speech_service = get_speech_service()
        text = await speech_service.speech_to_text_from_audio(audio_data)
        
        if text:
            return {
                "success": True,
                "text": text
            }
        else:
            return {
                "success": False,
                "text": "",
                "message": "No speech recognized"
            }
            
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT error: {str(e)}")

@app.post("/api/session/configure")
async def configure_session(request: SessionConfigRequest):
    """
    Configure interview session based on candidate profile.
    Returns personalized problem and introduction.
    """
    try:
        from app.agents.plugins.problem_generator_plugin import (
            ProblemGeneratorPlugin, 
            InterviewCustomizerPlugin
        )
        
        problem_gen = ProblemGeneratorPlugin()
        customizer = InterviewCustomizerPlugin()
        
        # Assess candidate level
        assessment = problem_gen.assess_experience_level(
            years_experience=request.experience_years,
            skills=request.skills,
            education="not_specified"
        )
        
        # Generate personalized introduction
        intro = customizer.generate_introduction(
            candidate_name=request.candidate_name,
            target_role=request.target_role,
            experience_years=request.experience_years
        )
        
        # Generate appropriate problem
        problem = problem_gen.generate_problem(
            experience_years=request.experience_years,
            target_role=request.target_role,
            focus_area=request.focus_area or ""
        )
        
        return {
            "success": True,
            "candidate_level": assessment,
            "introduction": intro,
            "problem_guidance": problem
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session config error: {str(e)}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "AI Interview Platform",
        "version": settings.API_VERSION,
        "features": ["tts", "stt", "dynamic_problems", "agentic_ai"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint to verify backend and services"""
    status = {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "judge0": "unknown",
            "azure_speech": "unknown"
        }
    }
    
    # Check Judge0
    try:
        async with aiohttp.ClientSession() as session:
            judge0_url = f"{settings.JUDGE0_ENDPOINT}/about"
            async with session.get(judge0_url, timeout=2) as response:
                status["services"]["judge0"] = "connected" if response.status == 200 else f"error: {response.status}"
    except Exception as e:
        status["services"]["judge0"] = f"unreachable: {str(e)}"
    
    # Check Azure Speech
    if settings.AZURE_SPEECH_KEY and settings.AZURE_SPEECH_REGION:
        status["services"]["azure_speech"] = "configured"
    else:
        status["services"]["azure_speech"] = "not_configured"

    return status

