"""
Configuration management for the AI Interview Platform
Loads environment variables and provides centralized config access
"""
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    API_TITLE: str = "AI Interview Platform API"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # CORS Settings
    CORS_ORIGINS: list = ["*"]
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_DEPLOYMENT: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    # Azure Speech Services (TTS/STT)
    AZURE_SPEECH_KEY: str = os.getenv("AZURE_SPEECH_KEY", "")
    AZURE_SPEECH_REGION: str = os.getenv("AZURE_SPEECH_REGION", "eastus")
    
    # Standard OpenAI Configuration (Fallback)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Local LLM (Ollama)
    USE_LOCAL_LLM: bool = os.getenv("USE_LOCAL_LLM", "False").lower() == "true"
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    
    # Judge0 Configuration
    JUDGE0_API_KEY: str = os.getenv("JUDGE0_API_KEY", "")
    JUDGE0_ENDPOINT: str = os.getenv("JUDGE0_ENDPOINT", "https://judge0-ce.p.rapidapi.com")
    
    # Session Configuration
    SESSION_TIMEOUT_MINUTES: int = 60
    CODE_UPDATE_DEBOUNCE_MS: int = 500
    
    # Stuck Detection Thresholds
    STUCK_ERROR_THRESHOLD: int = 3  # Same error 3 times triggers hint
    STUCK_IDLE_SECONDS: int = 120   # 2 minutes no code change after error
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()
