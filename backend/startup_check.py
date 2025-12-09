"""
Quick startup script to check backend configuration
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

print("\n" + "="*60)
print("🚀 AI INTERVIEW PLATFORM - STARTING UP")
print("="*60)

print("\n📋 Configuration Check:")
print(f"   DEBUG: {settings.DEBUG}")
print(f"   API Title: {settings.API_TITLE}")
print(f"   CORS Origins: {settings.CORS_ORIGINS}")

print("\n🤖 AI Configuration:")
if settings.USE_LOCAL_LLM:
    print(f"   ✅ Using Local LLM (Ollama): {settings.OLLAMA_MODEL}")
    print(f"   📍 Ollama URL: {settings.OLLAMA_BASE_URL}")
else:
    if settings.OPENAI_API_KEY:
        print(f"   ✅ Using OpenAI API")
    else:
        print(f"   ⚠️  No OpenAI API Key configured!")

print("\n⚙️  Judge0 Configuration:")
if settings.JUDGE0_API_KEY:
    print(f"   ✅ Judge0 configured: {settings.JUDGE0_ENDPOINT}")
else:
    print(f"   ⚠️  No Judge0 API Key!")

print("\n" + "="*60)
print("✅ Configuration loaded successfully!")
print("="*60 + "\n")

print("Starting Uvicorn server...")
print("Backend will be available at: http://localhost:8000")
print("Frontend should connect to: ws://localhost:8000/socket.io\n")
