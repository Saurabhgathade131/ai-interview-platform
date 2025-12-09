@echo off
echo Installing dependencies...
pip install fastapi aiohttp python-socketio pydantic-settings python-dotenv openai uvicorn
echo.
echo Starting Backend Server (Stable Mode)...
python run_server_no_reload.py
pause
