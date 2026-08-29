import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from current directory
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

class Config:
    # Telegram settings
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8631760685:AAFASOgBW_mx2Kgd_6UMCCw4SCv9ToXO9rc").strip().strip("\"'")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip().strip("\"'")

    # AI Model settings (Gemini API - Optional)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip().strip("\"'")

    # Crypto APIs (Optional)
    CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY", "").strip().strip("\"'")
    COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "").strip().strip("\"'")

    # Notification interval (in hours) for automatic popups
    DAILY_DIGEST_INTERVAL_HOURS = int(os.getenv("DAILY_DIGEST_INTERVAL_HOURS", "6"))
