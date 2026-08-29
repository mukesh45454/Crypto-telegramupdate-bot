import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from current directory
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

class Config:
    # Telegram settings
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip().strip("\"'")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip().strip("\"'")

    # AI Model settings (Groq AI & Gemini)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip().strip("\"'")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip().strip("\"'")

    # Crypto APIs (Optional)
    CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY", "").strip().strip("\"'")
    COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "").strip().strip("\"'")

    # Notification interval (in hours) for automatic popups
    DAILY_DIGEST_INTERVAL_HOURS = int(os.getenv("DAILY_DIGEST_INTERVAL_HOURS", "6"))
