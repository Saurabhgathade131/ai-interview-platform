import asyncio
import os
from openai import AsyncOpenAI

# Configuration
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "llama3.2"
API_KEY = "ollama"

async def test_stream():
    print(f"Connecting to Ollama at {OLLAMA_BASE_URL}...")
    
    client = AsyncOpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key=API_KEY
    )
    
    try:
        stream = await client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": "Say hello!"}],
            stream=True
        )
        
        print("Stream started.")
        full_text = ""
        async for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta.content:
                    print(f"CHUNK: '{delta.content}'")
                    full_text += delta.content
        
        print(f"FULL TEXT: {full_text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_stream())
