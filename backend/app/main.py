"""
Main FastAPI application with Socket.io integration
This is the entry point for the backend server
"""
from datetime import datetime
import json
import aiohttp
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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
    allow_origins=settings.CORS_ORIGINS,
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

# Request model for running code
class RunCodeRequest(BaseModel):
    session_id: str
    code: str
    problem_id: str

@app.post("/api/run_code")
async def run_code_api(request: RunCodeRequest):
    """
    Execute code via Judge0 (REST API)
    """
    try:
        from app.services.judge0_service import Judge0Service
        judge = Judge0Service()
        result = await judge.execute_code(request.code, request.problem_id)
        return result
    except Exception as e:
        return {"status": "error", "stderr": str(e)}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "AI Interview Platform",
        "version": settings.API_VERSION
    }

@app.get("/health")
async def health_check():
    """Health check endpoint to verify backend and services"""
    status = {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "judge0": "unknown"
        }
    }
    
    # Check Judge0
    try:
        async with aiohttp.ClientSession() as session:
            # Check local versions endpoint or plain access
            judge0_url = f"{settings.JUDGE0_ENDPOINT}/about"
            
            async with session.get(judge0_url, timeout=2) as response:
                if response.status == 200:
                    status["services"]["judge0"] = "connected"
                else:
                    status["services"]["judge0"] = f"error: {response.status}"
    except Exception as e:
        status["services"]["judge0"] = f"unreachable: {str(e)}"

    return status
