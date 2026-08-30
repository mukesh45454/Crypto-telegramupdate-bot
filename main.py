import os
import json
import time
import logging
import threading
import requests
from flask import Flask, request, jsonify
from config import Config
from crypto_market import CryptoMarketData
from crypto_news import CryptoNewsFetcher
from ai_analysis import AIAnalysisEngine
from notifier_service import add_subscriber, run_notifier_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

TOKEN = Config.TELEGRAM_BOT_TOKEN
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

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
        r = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
        return r.json()
    except Exception as e:
        logger.error(f"Error sending message to {chat_id}: {e}")
        return None

def edit_message(chat_id, message_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        r = requests.post(f"{API_URL}/editMessageText", json=payload, timeout=10)
        return r.json()
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        return None

def answer_callback(callback_query_id):
    try:
        requests.post(f"{API_URL}/answerCallbackQuery", json={"callback_query_id": callback_query_id}, timeout=5)
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

def handle_coin(chat_id, coin_query, message_id=None):
    if not message_id:
        res = send_message(chat_id, f"⚡ <i>Analyzing <b>{coin_query.upper()}</b> market data, news & future scope...</i>")
        message_id = res.get("result", {}).get("message_id") if res else None

    market_data = CryptoMarketData.get_coin_overview(coin_query)
    if not market_data:
        err_msg = f"❌ Could not locate crypto data for <b>'{coin_query}'</b>.\nPlease check symbol or name (e.g. <code>btc</code>, <code>sol</code>, <code>beldex</code>)."
        if message_id:
            res_edit = edit_message(chat_id, message_id, err_msg)
            if not res_edit or not res_edit.get("ok"):
                send_message(chat_id, err_msg)
        else:
            send_message(chat_id, err_msg)
        return

    news = CryptoNewsFetcher.get_news_for_coin(market_data["name"], market_data["symbol"], 3)
    insights = AIAnalysisEngine.generate_coin_insights(market_data, news)
    report_html = AIAnalysisEngine.format_full_report_html(market_data, news, insights)

    refresh_kb = {
        "inline_keyboard": [
            [{"text": f"🔄 Refresh {market_data['symbol']}", "callback_data": f"coin:{market_data['id']}"}],
            [{"text": "🔙 Main Menu", "callback_data": "cmd:start"}]
        ]
    }

    if message_id:
        res_edit = edit_message(chat_id, message_id, report_html, reply_markup=refresh_kb)
        if not res_edit or not res_edit.get("ok"):
            send_message(chat_id, report_html, reply_markup=refresh_kb)
    else:
        send_message(chat_id, report_html, reply_markup=refresh_kb)

import re

def parse_user_query(text: str):
    t = text.lower().strip()
    if t == "/start":
        return "start", ""
    if t in ["hi", "hello", "hey", "help", "menu", "start", "/menu"]:
        return "menu", ""
    if any(k in t for k in ["trending", "top coin", "hot coin", "gainers"]):
        return "trending", ""
    if any(k in t for k in ["digest", "overview", "all coins", "popup", "pop-up"]):
        return "digest", ""
    if t in ["news", "/news", "crypto news", "breaking news", "headlines"]:
        return "news", ""
    
    cleaned = t
    for phrase in ["tell me about", "what is", "future scope of", "future scope", "future of", "price of", "rate of", "update on", "updates on", "analysis of", "prediction of", "news on", "news about", "info on", "info about", "details of", "details on", "/crypto"]:
        cleaned = cleaned.replace(phrase, " ")
    cleaned = re.sub(r"\b(coin|coins|token|tokens|crypto|cryptocurrency|price|news|rate|rates|update|updates|future|scope|analyze|analysis|prediction|predictions|details|info)\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip(" ?.!/\\,:-_")
    tokens = cleaned.split()
    if tokens:
        return "coin", tokens[0]
    return "coin", t

def process_single_update(u):
    """Processes any incoming Telegram update object immediately in a background worker."""
    try:
        # 1. Handle Callback Query (Buttons)
        if "callback_query" in u:
            cb = u["callback_query"]
            cb_id = cb["id"]
            chat_id = cb["message"]["chat"]["id"]
            msg_id = cb["message"]["message_id"]
            data_val = cb["data"]
            answer_callback(cb_id)

            if data_val.startswith("coin:"):
                coin = data_val.split(":")[1]
                edit_message(chat_id, msg_id, f"⚡ <i>Analyzing <b>{coin.capitalize()}</b>...</i>")
                handle_coin(chat_id, coin, message_id=msg_id)
            elif data_val == "cmd:trending":
                trending = CryptoMarketData.get_trending_coins()
                text = "🔥 <b>TOP TRENDING CRYPTOCURRENCIES:</b>\n\n"
                for t in trending:
                    text += f"• <b>{t['name']} ({t['symbol']})</b> - Rank #{t['rank']}\n"
                edit_message(chat_id, msg_id, text, reply_markup=get_main_keyboard())
            elif data_val == "cmd:news":
                headlines = CryptoNewsFetcher.get_market_headlines(limit=4)
                text = "📰 <b>BREAKING CRYPTO NEWS:</b>\n\n"
                for h in headlines:
                    title = h['title'].replace("<", "&lt;").replace(">", "&gt;")
                    text += f"• <a href='{h['link']}'>{title}</a> <i>({h['source']})</i>\n\n"
                edit_message(chat_id, msg_id, text, reply_markup=get_main_keyboard())
            elif data_val == "cmd:digest":
                coins = ["bitcoin", "ethereum", "solana", "beldex"]
                lines = ["🌅 <b>POP-UP CRYPTO MARKET DIGEST</b> 🌅\n"]
                for c in coins:
                    d = CryptoMarketData.get_coin_overview(c)
                    if d:
                        trend = "🟢 📈" if d['change_24h'] >= 0 else "🔴 📉"
                        sign = "+" if d['change_24h'] >= 0 else ""
                        lines.append(f"• <b>{d['name']} ({d['symbol']})</b>: ${d['price_usd']:,.2f} USD (₹{d['price_inr']:,.2f})\n  24h Change: {trend} <b>{sign}{d['change_24h']}%</b> | Rank #{d['rank']}")
                lines.append("\n<i>Tap any coin button above or type any coin name for full future scope & utility!</i>")
                edit_message(chat_id, msg_id, "\n".join(lines), reply_markup=get_main_keyboard())
            elif data_val == "cmd:start":
                edit_message(chat_id, msg_id, "🚀 <b>Main Menu:</b>", reply_markup=get_main_keyboard())
            return

        # 2. Handle Text Messages
        if "message" in u and "text" in u["message"]:
            msg = u["message"]
            chat_id = msg["chat"]["id"]
            text = msg["text"].strip()
            user_name = msg.get("from", {}).get("first_name", "Trader")
            
            add_subscriber(chat_id)
            intent, target = parse_user_query(text)

            if intent == "start":
                welcome_text = f"""👋 <b>Welcome, {user_name}!</b>

🔔 <i>You are registered for live crypto intelligence pop-up updates!</i>

<b>What I provide for ANY cryptocurrency:</b>
• 📊 <b>Live Market Price & Metrics</b> (USD & INR, 24h change, ATH, Rank)
• 📰 <b>Updated News & Roadmaps</b>
• 💡 <b>Major Benefits & Real-World Utility</b>
• 🚀 <b>Future Scope & Long-Term Potential</b>

Tap a button below or simply type any coin (e.g. <i>'Bitcoin'</i>, <i>'Solana'</i>, <i>'Beldex'</i>):"""
                send_message(chat_id, welcome_text, reply_markup=get_main_keyboard())

            elif intent == "menu":
                send_message(chat_id, f"👋 Hello {user_name}! Type any crypto name (e.g. <b>Bitcoin</b>, <b>Ethereum</b>, <b>Beldex</b>, <b>Solana</b>) or choose from the menu below:", reply_markup=get_main_keyboard())

            elif intent == "news":
                headlines = CryptoNewsFetcher.get_market_headlines(limit=5)
                text_resp = "📰 <b>TOP CRYPTO MARKET BREAKING NEWS</b>\n\n"
                for h in headlines:
                    title = h['title'].replace("<", "&lt;").replace(">", "&gt;")
                    text_resp += f"• <a href='{h['link']}'>{title}</a>\n  <i>Source: {h['source']} | {h['published']}</i>\n\n"
                send_message(chat_id, text_resp, reply_markup=get_main_keyboard())

            elif intent == "trending":
                trending = CryptoMarketData.get_trending_coins()
                text_resp = "🔥 <b>TOP TRENDING CRYPTOCURRENCIES:</b>\n\n"
                for t in trending:
                    text_resp += f"• <b>{t['name']} ({t['symbol']})</b> - Rank #{t['rank']}\n"
                send_message(chat_id, text_resp, reply_markup=get_main_keyboard())

            elif intent == "digest":
                coins = ["bitcoin", "ethereum", "solana", "beldex"]
                lines = ["🌅 <b>POP-UP CRYPTO MARKET DIGEST & UPDATE</b> 🌅\n"]
                for c in coins:
                    d = CryptoMarketData.get_coin_overview(c)
                    if d:
                        trend = "🟢 📈" if d['change_24h'] >= 0 else "🔴 📉"
                        sign = "+" if d['change_24h'] >= 0 else ""
                        lines.append(f"• <b>{d['name']} ({d['symbol']})</b>: ${d['price_usd']:,.2f} USD (₹{d['price_inr']:,.2f})\n  24h Change: {trend} <b>{sign}{d['change_24h']}%</b> | Rank #{d['rank']}")
                lines.append("\n<i>Tap any coin button below or type any coin name for full future scope & utility!</i>")
                send_message(chat_id, "\n".join(lines), reply_markup=get_main_keyboard())

            elif intent == "coin":
                handle_coin(chat_id, target)

    except Exception as e:
        logger.error(f"Error processing update: {e}")

# ==========================================================
# FLASK WEBHOOK ENDPOINTS (FOR INSTANT 0-DELAY CLOUD RESPONSES)
# ==========================================================

@app.route("/", methods=["GET"])
def health_check():
    return "✅ Crypto Intelligence Telegram Bot is Online 24/7 & Active!", 200

@app.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():
    """Telegram delivers updates directly here in real-time (<10ms non-blocking acknowledgment)!"""
    try:
        update_data = request.get_json(force=True, silent=True)
        if update_data:
            # Spawn worker thread immediately to avoid Telegram timeout
            threading.Thread(target=process_single_update, args=(update_data,), daemon=True).start()
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
    return jsonify({"status": "ok"}), 200

def setup_webhook_if_cloud():
    """Ensures Telegram Webhook is active for real-time instant responses."""
    render_url = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("WEBHOOK_URL") or "https://crypto-telegramupdate-bot.onrender.com"
    if render_url:
        webhook_endpoint = f"{render_url.rstrip('/')}/telegram-webhook"
        logger.info(f"Setting Telegram Webhook to: {webhook_endpoint}")
        try:
            r = requests.post(f"{API_URL}/setWebhook", json={"url": webhook_endpoint}, timeout=10)
            logger.info(f"Telegram Webhook setup response: {r.json()}")
            return True
        except Exception as e:
            logger.error(f"Error setting Telegram Webhook: {e}")
    return False

def polling_loop():
    """High speed fallback polling loop when not using webhooks."""
    try:
        requests.post(f"{API_URL}/deleteWebhook", timeout=5)
    except Exception:
        pass

    logger.info("Starting High-Speed Telegram Poller Engine...")
    offset = 0
    while True:
        try:
            r = requests.get(f"{API_URL}/getUpdates?offset={offset}&timeout=20", timeout=25)
            if r.status_code != 200:
                time.sleep(1)
                continue

            data = r.json()
            if not data.get("ok"):
                time.sleep(1)
                continue

            updates = data.get("result", [])
            for u in updates:
                offset = u["update_id"] + 1
                threading.Thread(target=process_single_update, args=(u,), daemon=True).start()

        except Exception as e:
            logger.error(f"Error in poll loop: {e}")
            time.sleep(2)

def run_bot():
    # 1. Start Notifier loop in background
    notifier_thread = threading.Thread(
        target=run_notifier_loop,
        args=(Config.DAILY_DIGEST_INTERVAL_HOURS,),
        daemon=True
    )
    notifier_thread.start()

    # 2. Check if we have a cloud webhook URL
    is_webhook = setup_webhook_if_cloud()
    if not is_webhook:
        poll_thread = threading.Thread(target=polling_loop, daemon=True)
        poll_thread.start()

    # 3. Start Flask Web Server
    port = int(os.getenv("PORT", "10000"))
    logger.info(f"Starting Webhook & Health server on port {port}...")
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    run_bot()
