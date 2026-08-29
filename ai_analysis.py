import re
import logging
import requests
from typing import Dict, Any, List
from config import Config

logger = logging.getLogger(__name__)

KNOWLEDGE_BASE = {
    "bitcoin": {
        "benefits": [
            "Digital Gold & Hard Store of Value with hard-capped 21 Million supply.",
            "Decentralized, trustless, and permissionless financial network resistant to censorship.",
            "Institutional adoption as reserve treasury asset (ETFs, corporate balance sheets).",
            "Lightning Network layer-2 scaling for near-instant, low-cost global micro-payments."
        ],
        "project_updates": [
            "Mainnet protocol stability with ongoing Layer-2 scaling and institutional ETF adoption.",
            "Taproot upgrade adoption enhancing privacy, multisig, and scripting efficiency."
        ],
        "future_scope": [
            "Value Outlook: Foundational global digital reserve asset of the modern economy.",
            "Adoption Catalysts: Sovereign wealth adoption, pension fund allocations, and cross-border settlement."
        ]
    }
}

class AIAnalysisEngine:

    @classmethod
    def generate_coin_insights(cls, coin_data: Dict[str, Any], news_items: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Synthesizes deep crypto intelligence using Groq AI (OpenAI GPT-OSS / Qwen).
        """
        coin_id = coin_data.get("id", "").lower()
        coin_name = coin_data.get("name", "")
        coin_symbol = coin_data.get("symbol", "")
        price_usd = coin_data.get("price_usd", 0)
        change_24h = coin_data.get("change_24h", 0)
        rank = coin_data.get("rank", "N/A")

        # 1. Groq AI Integration (Ultra-fast & In-depth)
        if Config.GROQ_API_KEY:
            try:
                news_snippet = "\n".join([f"- {n['title']}" for n in news_items[:3]])
                prompt = f"""You are a senior cryptocurrency analyst. Analyze {coin_name} ({coin_symbol}):
Price: ${price_usd} USD, 24h Change: {change_24h}%, Market Rank: #{rank}
Recent News:
{news_snippet}

Output in exactly 3 sections:
💡 MAJOR BENEFITS & UTILITY:
• (3 concise bullet points on technology, utility, problem solved)

🛠️ PROJECT & ECOSYSTEM UPDATES:
• (2-3 concise bullet points on roadmap, protocol upgrades, ecosystem)

🚀 FUTURE SCOPE & VALUE POTENTIAL:
• (2-3 concise bullet points on long-term price potential, adoption catalysts, risks)
"""
                headers = {
                    "Authorization": f"Bearer {Config.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "openai/gpt-oss-120b",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
                resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10)
                if resp.status_code == 200:
                    ai_content = resp.json()['choices'][0]['message']['content'].strip()
                    ai_content = re.sub(r"<think>.*?</think>", "", ai_content, flags=re.DOTALL).strip()
                    if ai_content:
                        return {
                            "ai_generated": True,
                            "content": ai_content
                        }
            except Exception as e:
                logger.warning(f"Groq AI error, falling back: {e}")

        # 2. Curated Fallback
        kb = KNOWLEDGE_BASE.get(coin_id) or KNOWLEDGE_BASE.get(coin_symbol.lower())
        if kb:
            benefits = kb["benefits"]
            project_updates = kb["project_updates"]
            future_scope = kb["future_scope"]
        else:
            benefits = [
                f"{coin_name} operates as a decentralized blockchain asset providing network utility.",
                f"Global market rank #{rank} with active exchange trading pairs."
            ]
            project_updates = [
                f"Ongoing network transactions and active protocol maintenance on {coin_name}."
            ]
            future_scope = [
                f"Long-term value driven by Web3 adoption, user growth, and market liquidity."
            ]

        content = f"""💡 <b>MAJOR BENEFITS & UTILITY:</b>
{chr(10).join(['• ' + b for b in benefits])}

🛠️ <b>PROJECT & ECOSYSTEM UPDATES:</b>
{chr(10).join(['• ' + p for p in project_updates])}

🚀 <b>FUTURE SCOPE & VALUE POTENTIAL:</b>
{chr(10).join(['• ' + f for f in future_scope])}"""

        return {
            "ai_generated": False,
            "content": content
        }

    @classmethod
    def format_full_report_html(cls, coin_data: Dict[str, Any], news_items: List[Dict[str, str]], insights: Dict[str, Any]) -> str:
        name = coin_data.get("name", "Crypto")
        sym = coin_data.get("symbol", "")
        price_usd = coin_data.get("price_usd", 0)
        price_inr = coin_data.get("price_inr", 0)
        chg_24h = coin_data.get("change_24h", 0)
        rank = coin_data.get("rank", "N/A")
        mcap = coin_data.get("market_cap_usd", 0)
        ath = coin_data.get("ath_usd", 0)
        ath_change = coin_data.get("ath_change_pct", 0)
        high_24h = coin_data.get("high_24h", 0)
        low_24h = coin_data.get("low_24h", 0)

        trend_emoji = "🟢 📈" if chg_24h >= 0 else "🔴 📉"
        change_sign = "+" if chg_24h >= 0 else ""

        def format_currency(num):
            if num >= 1_000_000_000:
                return f"${num/1_000_000_000:.2f}B"
            elif num >= 1_000_000:
                return f"${num/1_000_000:.2f}M"
            elif num >= 1_000:
                return f"${num/1_000:.2f}K"
            elif num > 0:
                return f"${num:,.4f}"
            return "N/A"

        news_section = ""
        if news_items:
            news_section = "\n📰 <b>RECENT UPDATED NEWS & HEADLINES:</b>\n"
            for n in news_items[:3]:
                title = n['title'].replace("<", "&lt;").replace(">", "&gt;")
                news_section += f"• <a href='{n['link']}'>{title}</a> <i>({n['source']})</i>\n"
        else:
            news_section = "\n📰 <b>RECENT NEWS:</b> Active market volume observed.\n"

        ai_text = insights.get("content", "")
        if insights.get("ai_generated"):
            # Escape HTML characters first
            ai_text = ai_text.replace("<", "&lt;").replace(">", "&gt;")
            # Convert Markdown to clean Telegram HTML
            ai_text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", ai_text)
            ai_text = re.sub(r"### (.*?)\n", r"<b>\1</b>\n", ai_text)
            ai_text = re.sub(r"## (.*?)\n", r"<b>\1</b>\n", ai_text)

        msg = f"""🔥 <b>{name} ({sym}) MARKET & FUTURE SCOPE INTELLIGENCE</b> 🔥

📊 <b>CURRENT MARKET UPDATE:</b>
• <b>Price:</b> ${price_usd:,.4f} USD | ₹{price_inr:,.2f} INR
• <b>24h Change:</b> {trend_emoji} <b>{change_sign}{chg_24h}%</b>
• <b>24h Range:</b> ${low_24h:,.4f} - ${high_24h:,.4f}
• <b>Market Cap:</b> {format_currency(mcap)} (Rank #{rank})
• <b>All-Time High:</b> ${ath:,.2f} ({ath_change}%)
{news_section}
{ai_text}

⚡ <i>Powered by Groq AI & Crypto Intelligence Engine</i>"""
        return msg.strip()
