import sys
import os
import time
import logging
import requests
from config import Config
from crypto_market import CryptoMarketData
from crypto_news import CryptoNewsFetcher
from ai_analysis import AIAnalysisEngine
from notifier_service import add_subscriber

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

TOKEN = Config.TELEGRAM_BOT_TOKEN
API_URL = f"https://api.telegram.org/bot{TOKEN}"

def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        r = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=15)
        return r.json()
    except Exception as e:
        logger.error(f"Error sending message to {chat_id}: {e}")
        return None

def answer_callback(callback_query_id):
    try:
        requests.post(f"{API_URL}/answerCallbackQuery", json={"callback_query_id": callback_query_id}, timeout=10)
    except Exception:
        pass

def get_main_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "🟠 Bitcoin (BTC)", "callback_data": "coin:bitcoin"},
                {"text": "🔷 Ethereum (ETH)", "callback_data": "coin:ethereum"}
            ],
            [
                {"text": "🟣 Solana (SOL)", "callback_data": "coin:solana"},
                {"text": "🛡️ Beldex (BDX)", "callback_data": "coin:beldex"}
            ],
            [
                {"text": "🔥 Trending Coins", "callback_data": "cmd:trending"},
                {"text": "📰 Breaking News", "callback_data": "cmd:news"}
            ],
            [
                {"text": "📊 Instant Market Digest", "callback_data": "cmd:digest"}
            ]
        ]
    }

def handle_coin(chat_id, coin_query):
    send_message(chat_id, f"🔍 <i>Analyzing market stats, news & future scope for <b>'{coin_query}'</b>...</i>")
    market_data = CryptoMarketData.get_coin_overview(coin_query)
    if not market_data:
        send_message(chat_id, f"❌ Could not locate crypto data for <b>'{coin_query}'</b>.\nPlease check symbol or name (e.g. <code>btc</code>, <code>sol</code>, <code>beldex</code>).")
        return

    news = CryptoNewsFetcher.get_news_for_coin(market_data["name"], market_data["symbol"], limit=3)
    insights = AIAnalysisEngine.generate_coin_insights(market_data, news)
    report_html = AIAnalysisEngine.format_full_report_html(market_data, news, insights)

    refresh_kb = {
        "inline_keyboard": [
            [{"text": f"🔄 Refresh {market_data['symbol']}", "callback_data": f"coin:{market_data['id']}"}],
            [{"text": "🔙 Main Menu", "callback_data": "cmd:start"}]
        ]
    }
    send_message(chat_id, report_html, reply_markup=refresh_kb)

def process_updates():
    logger.info("Starting Telegram Poller Engine...")
    offset = 0
    while True:
        try:
            r = requests.get(f"{API_URL}/getUpdates?offset={offset}&timeout=20", timeout=25)
            if r.status_code != 200:
                time.sleep(2)
                continue

            data = r.json()
            if not data.get("ok"):
                time.sleep(2)
                continue

            updates = data.get("result", [])
            for u in updates:
                offset = u["update_id"] + 1

                # 1. Handle Callback Query (Buttons)
                if "callback_query" in u:
                    cb = u["callback_query"]
                    cb_id = cb["id"]
                    chat_id = cb["message"]["chat"]["id"]
                    data_val = cb["data"]
                    answer_callback(cb_id)

                    if data_val.startswith("coin:"):
                        coin = data_val.split(":")[1]
                        handle_coin(chat_id, coin)
                    elif data_val == "cmd:trending":
                        trending = CryptoMarketData.get_trending_coins()
                        text = "🔥 <b>TOP TRENDING COINS:</b>\n\n"
                        for t in trending:
                            text += f"• <b>{t['name']} ({t['symbol']})</b> - Rank #{t['rank']}\n"
                        send_message(chat_id, text, reply_markup=get_main_keyboard())
                    elif data_val == "cmd:news":
                        headlines = CryptoNewsFetcher.get_market_headlines(limit=4)
                        text = "📰 <b>BREAKING CRYPTO NEWS:</b>\n\n"
                        for h in headlines:
                            title = h['title'].replace("<", "&lt;").replace(">", "&gt;")
                            text += f"• <a href='{h['link']}'>{title}</a> <i>({h['source']})</i>\n\n"
                        send_message(chat_id, text, reply_markup=get_main_keyboard())
                    elif data_val == "cmd:digest":
                        coins = ["bitcoin", "ethereum", "solana", "beldex"]
                        lines = ["🌅 <b>POP-UP CRYPTO MARKET DIGEST</b> 🌅\n"]
                        for c in coins:
                            d = CryptoMarketData.get_coin_overview(c)
                            if d:
                                trend = "🟢 📈" if d['change_24h'] >= 0 else "🔴 📉"
                                sign = "+" if d['change_24h'] >= 0 else ""
                                lines.append(f"• <b>{d['name']} ({d['symbol']})</b>: ${d['price_usd']:,.2f} | {trend} {sign}{d['change_24h']}%")
                        send_message(chat_id, "\n".join(lines), reply_markup=get_main_keyboard())
                    elif data_val == "cmd:start":
                        send_message(chat_id, "🚀 <b>Main Menu:</b>", reply_markup=get_main_keyboard())
                    continue

                # 2. Handle Text Messages
                if "message" in u and "text" in u["message"]:
                    msg = u["message"]
                    chat_id = msg["chat"]["id"]
                    text = msg["text"].strip()
                    user_name = msg.get("from", {}).get("first_name", "Trader")
                    
                    add_subscriber(chat_id)

                    if text.startswith("/start"):
                        welcome_text = f"""👋 <b>Welcome, {user_name}!</b>

🔔 <i>You are registered for live crypto intelligence pop-up updates!</i>

<b>What I provide for ANY cryptocurrency:</b>
• 📊 <b>Live Market Price & Metrics</b> (USD & INR, 24h change, ATH, Rank)
• 📰 <b>Updated News & Roadmaps</b>
• 💡 <b>Major Benefits & Real-World Utility</b>
• 🚀 <b>Future Scope & Long-Term Potential</b>

Tap a button below or simply type any coin (e.g. <i>'Bitcoin'</i>, <i>'Solana'</i>, <i>'Beldex'</i>):"""
                        send_message(chat_id, welcome_text, reply_markup=get_main_keyboard())

                    elif text.startswith("/crypto"):
                        parts = text.split(maxsplit=1)
                        if len(parts) > 1:
                            handle_coin(chat_id, parts[1])
                        else:
                            send_message(chat_id, "⚠️ Please specify a coin: e.g., <code>/crypto bitcoin</code> or <code>/crypto bdx</code>")

                    elif text.startswith("/news"):
                        headlines = CryptoNewsFetcher.get_market_headlines(limit=5)
                        text_resp = "📰 <b>TOP CRYPTO MARKET BREAKING NEWS</b>\n\n"
                        for h in headlines:
                            title = h['title'].replace("<", "&lt;").replace(">", "&gt;")
                            text_resp += f"• <a href='{h['link']}'>{title}</a>\n  <i>Source: {h['source']} | {h['published']}</i>\n\n"
                        send_message(chat_id, text_resp)

                    elif text.startswith("/trending"):
                        trending = CryptoMarketData.get_trending_coins()
                        text_resp = "🔥 <b>TOP TRENDING COINS:</b>\n\n"
                        for t in trending:
                            text_resp += f"• <b>{t['name']} ({t['symbol']})</b> - Rank #{t['rank']}\n"
                        send_message(chat_id, text_resp)

                    elif text.startswith("/digest"):
                        coins = ["bitcoin", "ethereum", "solana", "beldex"]
                        lines = ["🌅 <b>POP-UP CRYPTO MARKET DIGEST & UPDATE</b> 🌅\n"]
                        for c in coins:
                            d = CryptoMarketData.get_coin_overview(c)
                            if d:
                                trend = "🟢 📈" if d['change_24h'] >= 0 else "🔴 📉"
                                sign = "+" if d['change_24h'] >= 0 else ""
                                lines.append(f"• <b>{d['name']} ({d['symbol']})</b>: ${d['price_usd']:,.2f} USD (₹{d['price_inr']:,.2f})\n  24h Change: {trend} <b>{sign}{d['change_24h']}%</b> | Rank #{d['rank']}")
                        send_message(chat_id, "\n".join(lines), reply_markup=get_main_keyboard())

                    elif text.lower() in ["hi", "hello", "hey", "help", "menu"]:
                        send_message(chat_id, f"👋 Hello {user_name}! Type any crypto name (e.g. <b>Bitcoin</b>, <b>Ethereum</b>, <b>Beldex</b>, <b>Solana</b>) or select from the menu below:", reply_markup=get_main_keyboard())

                    else:
                        # Natural language query like "tell me about bitcoin"
                        cleaned = text.lower()
                        for prefix in ["tell me about", "what is", "future of", "price of", "crypto", "analyze", "update on"]:
                            cleaned = cleaned.replace(prefix, "")
                        cleaned = cleaned.strip(" ?.!/\\")
                        if not cleaned:
                            cleaned = text
                        handle_coin(chat_id, cleaned)

        except Exception as e:
            logger.error(f"Error in poll loop: {e}")
            time.sleep(3)

if __name__ == "__main__":
    process_updates()
