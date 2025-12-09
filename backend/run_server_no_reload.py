import uvicorn
import os
import sys

# Ensure we can import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Starting server without reload for stability...")
    try:
        uvicorn.run("app.main:socket_app", host="0.0.0.0", port=8000, log_level="info", reload=False)
    except Exception as e:
        print(f"Server crashed: {e}")
        import traceback
        traceback.print_exc()
