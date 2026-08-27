import os
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from config import Config
from bot_service import process_updates
from notifier_service import run_notifier_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Lightweight Health Check Server for Render Free Web Service
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Crypto Intelligence Telegram Bot is running 24/7!")

    def log_message(self, format, *args):
        pass # Suppress noisy health check logs

def run_health_server():
    port = int(os.getenv("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    logger.info(f"Health check server running on port {port} for Render cloud...")
    server.serve_forever()

def main():
    print("==============================================================")
    print("   🚀 CRYPTO INTELLIGENCE TELEGRAM BOT (CLOUD 24/7 ENGINE)")
    print("==============================================================")
    print("🤖 Bot Username: @Master_cryp1bot")

    # 1. Start HTTP Health check thread (ensures Render Free tier stays active)
    http_thread = threading.Thread(target=run_health_server, daemon=True)
    http_thread.start()

    # 2. Start Scheduled Notifier thread
    notifier_thread = threading.Thread(
        target=run_notifier_loop, 
        args=(Config.DAILY_DIGEST_INTERVAL_HOURS,), 
        daemon=True
    )
    notifier_thread.start()

    # 3. Start Telegram Polling loop
    process_updates()

if __name__ == "__main__":
    main()
