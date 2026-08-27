import time
import json
import logging
import requests
from pathlib import Path
from typing import Set
from config import Config
from crypto_market import CryptoMarketData
from crypto_news import CryptoNewsFetcher
from ai_analysis import AIAnalysisEngine

logger = logging.getLogger(__name__)

SUBSCRIBERS_FILE = Path(__file__).resolve().parent / "subscribers.json"

def get_subscribers() -> Set[int]:
    """Loads all subscribed Telegram chat IDs."""
    subs = set()
    if Config.TELEGRAM_CHAT_ID:
        try:
            subs.add(int(Config.TELEGRAM_CHAT_ID))
        except ValueError:
            pass
    if SUBSCRIBERS_FILE.exists():
        try:
            with open(SUBSCRIBERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                subs.update(data)
        except Exception as e:
            logger.warning(f"Error reading subscribers: {e}")
    return subs

def add_subscriber(chat_id: int):
    """Registers a chat ID to receive automated pop-up notifications."""
    subs = get_subscribers()
    subs.add(chat_id)
    try:
        with open(SUBSCRIBERS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(subs), f)
    except Exception as e:
        logger.warning(f"Error saving subscriber: {e}")

def send_telegram_notification(chat_id: int, text: str) -> bool:
    """Sends notification pop-up directly via Telegram Bot HTTP API."""
    if not Config.TELEGRAM_BOT_TOKEN:
        logger.warning("Telegram Bot Token missing.")
        return False

    try:
        url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except Exception as e:
        logger.error(f"Error sending Telegram notification to {chat_id}: {e}")
        return False

def broadcast_market_digest():
    """Broadcasts automatic crypto market popup digest to all Telegram users."""
    subs = get_subscribers()
    if not subs:
        logger.info("No Telegram subscribers registered yet for scheduled popup.")
        return

    logger.info(f"Broadcasting market popup digest to {len(subs)} Telegram chats...")
    coins = ["bitcoin", "ethereum", "solana", "beldex"]
    
    lines = ["🌅 <b>CRYPTO MARKET & PROJECT UPDATE POPUP</b> 🌅\n"]

    for coin in coins:
        data = CryptoMarketData.get_coin_overview(coin)
        if data:
            trend = "🟢 📈" if data['change_24h'] >= 0 else "🔴 📉"
            sign = "+" if data['change_24h'] >= 0 else ""
            lines.append(
                f"• <b>{data['name']} ({data['symbol']})</b>: ${data['price_usd']:,.2f} USD (₹{data['price_inr']:,.2f})\n"
                f"  24h Change: {trend} <b>{sign}{data['change_24h']}%</b> | Rank #{data['rank']}"
            )

    lines.append("\n💡 <i>Tip: Send any coin name like 'bitcoin' or 'beldex' to get its full future scope, utility, and news!</i>")
    msg = "\n".join(lines)

    for chat_id in subs:
        send_telegram_notification(chat_id, msg)

def run_notifier_loop(interval_hours: int = 6):
    """Background notification worker loop."""
    interval_seconds = interval_hours * 3600
    logger.info(f"Telegram pop-up notifier active (every {interval_hours} hours).")
    while True:
        try:
            broadcast_market_digest()
        except Exception as e:
            logger.error(f"Error in notifier loop: {e}")
        time.sleep(interval_seconds)
