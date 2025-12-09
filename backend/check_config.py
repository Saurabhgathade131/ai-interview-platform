"""
Test script to verify Judge0 configuration
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(override=True)  # Force reload

from app.config import settings

print("\n" + "="*60)
print("🔍 JUDGE0 CONFIGURATION CHECK")
print("="*60)

print(f"\n📡 JUDGE0_ENDPOINT: {settings.JUDGE0_ENDPOINT}")
print(f"🔑 JUDGE0_API_KEY: {'✅ SET' if settings.JUDGE0_API_KEY else '❌ NOT SET'}")

print(f"\n🤖 AI CONFIGURATION:")
print(f"   USE_LOCAL_LLM: {settings.USE_LOCAL_LLM}")
if settings.USE_LOCAL_LLM:
    print(f"   Ollama Model: {settings.OLLAMA_MODEL}")
    print(f"   Ollama URL: {settings.OLLAMA_BASE_URL}")
else:
    print(f"   Using: {'Azure OpenAI' if settings.AZURE_OPENAI_API_KEY else 'Standard OpenAI'}")
    if settings.OPENAI_API_KEY:
        print(f"   OpenAI Key: ✅ SET (sk-proj-...{settings.OPENAI_API_KEY[-10:]})")
    else:
        print(f"   OpenAI Key: ❌ NOT SET")

print("\n" + "="*60)

# Verify correct endpoint
if "localhost" in settings.JUDGE0_ENDPOINT or "127.0.0.1" in settings.JUDGE0_ENDPOINT:
    print("❌ ERROR: Still using LOCAL endpoint!")
    print("   Judge0 will NOT work on Windows!")
    print("   Expected: https://judge0-ce.p.rapidapi.com")
    sys.exit(1)
elif "judge0-ce.p.rapidapi.com" in settings.JUDGE0_ENDPOINT:
    print("✅ CORRECT: Using hosted RapidAPI endpoint")
    if not settings.JUDGE0_API_KEY:
        print("⚠️  WARNING: API key is not set!")
    else:
        print(f"✅ API Key configured")
    print("\n🎉 Configuration is CORRECT!")
    print("   Code execution should work now!")
else:
    print(f"⚠️  Unknown endpoint: {settings.JUDGE0_ENDPOINT}")

print("="*60 + "\n")
