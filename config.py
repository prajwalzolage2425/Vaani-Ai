import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    """Application configuration for VaaniAI."""
    
    # Server settings
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
    SECRET_KEY = os.getenv("SECRET_KEY", "vaaniai-panini-shiksha-secret-key-2026")
    
    # MongoDB connection
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME = os.getenv("DB_NAME", "vaaniai")
    
    # Google Gemini API Settings (via google-genai SDK)
    # The model name is a single constant so it is easy to swap anytime
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # DEMO MODE:
    # When True, or when Gemini API fails / no key is provided,
    # realistic deterministic Shiksha results are returned for seeded demo phrases.
    # This guarantees the live exhibition presentation never breaks on stage!
    DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")
    
    # Audio uploads
    UPLOAD_FOLDER = BASE_DIR / "temp_audio"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max audio size
    ALLOWED_AUDIO_EXTENSIONS = {"webm", "wav", "mp3", "ogg", "m4a"}

# Ensure upload directory exists
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
