import logging
from typing import Dict, Any, List
from config import Config

logger = logging.getLogger(__name__)

# Built-in knowledge base for primary cryptos to ensure ultra-fast and reliable answers
KNOWLEDGE_BASE = {
    "bitcoin": {
        "benefits": [
            "Digital Gold & Hard Store of Value with hard-capped 21 Million supply.",
            "Decentralized, trustless, and permissionless financial network resistant to censorship.",
            "Institutional adoption as reserve treasury asset (ETFs, corporate balance sheets).",
            "Lightning Network layer-2 scaling for near-instant, low-cost global micro-payments."
        ],
        "project_updates": [
            "Mainnet protocol stability with ongoing Layer-2 (Lightning Network & Rootstock/Runes) scaling.",
            "Surging global Spot Bitcoin ETF inflows and sovereign wealth fund allocations.",
            "Taproot upgrade adoption enhancing privacy, multisig capabilities, and scripting efficiency."
        ],
        "future_scope": [
            "Value Outlook: Positioned as the foundational global reserve asset of the digital economy.",
            "Adoption Catalysts: Continued nation-state adoption, pension fund allocations, and cross-border settlement.",
            "Key Risks: Regulatory taxation policies and macroeconomic liquidity shifts."
        ]
    },
    "ethereum": {
        "benefits": [
            "The world leading programmable smart contract and decentralized application (dApp) platform.",
            "Settlement layer for the multi-billion dollar DeFi (Decentralized Finance) and tokenization economy.",
            "Proof-of-Stake consensus with deflationary 'Ultrasound Money' burn mechanism (EIP-1559).",
            "Massive developer ecosystem with the highest developer mindshare and tooling support."
        ],
        "project_updates": [
            "Dencun Upgrade (EIP-4844) dramatically reduced Layer-2 rollup gas fees via Proto-Danksharding.",
            "Pectra & Verge roadmap milestones focused on Verkle trees, account abstraction, and staking flexibility.",
            "Surging Real-World Asset (RWA) tokenization and spot Ethereum ETF participation."
        ],
        "future_scope": [
            "Value Outlook: Poised to remain the premier settlement layer for global financial institutions.",
            "Adoption Catalysts: Enterprise adoption of L2 networks (Base, Arbitrum, Optimism) and institutional staking.",
            "Key Risks: Competition from high-throughput monolithic L1s and Layer-2 fee capture dynamics."
        ]
    },
    "solana": {
        "benefits": [
            "Ultra-high throughput (up to 65,000 TPS) with sub-second finality and negligible transaction costs.",
            "Monolithic architecture avoiding complex Layer-2 fragmentation.",
            "Thriving ecosystem for high-frequency trading, consumer dApps, DeFi, and DePIN (Decentralized Physical Infrastructure).",
            "Mobile-first integration (Saga/Seeker web3 phones) driving mainstream mobile usability."
        ],
        "project_updates": [
            "Firedancer independent validator client release by Jump Crypto for unprecedented speed and reliability.",
            "Token Extensions enabling compliant enterprise asset issuance, confidential transfers, and hooks.",
            "Leading DEX volume and active user retention across decentralized finance."
        ],
        "future_scope": [
            "Value Outlook: High upside as the default high-performance execution layer for retail and fintech apps.",
            "Adoption Catalysts: Potential Spot Solana ETF approvals, institutional payment rails (Visa, Shopify), and DePIN growth.",
            "Key Risks: Network congestion during peak load and past historical network stability concerns."
        ]
    },
    "beldex": {
        "benefits": [
            "Privacy-first ecosystem with confidential transactions powered by ring signatures and stealth addresses.",
            "Decentralized Masternode network providing POS staking rewards and network validation.",
            "Decentralized privacy apps: BChat (private messenger), Belnet (dVPN), and Beldex Browser.",
            "EVM integration roadmap bringing privacy-preserving smart contracts."
        ],
        "project_updates": [
            "Deployment of Bern Hardfork and transition to Proof-of-Stake Masternodes.",
            "Advancements in the Beldex EVM (B-EVM) for private cross-chain decentralized applications.",
            "Expansion of Belnet decentralized onion routing protocol and BChat messaging network."
        ],
        "future_scope": [
            "Value Outlook: Significant niche growth potential as consumer demand for digital privacy and anti-censorship communication rises.",
            "Adoption Catalysts: Integration of Web3 privacy suite into everyday mobile devices and Web3 dApps.",
            "Key Risks: Privacy coin regulatory scrutiny and exchange listing liquidity."
        ]
    },
    "ripple": {
        "benefits": [
            "Instantaneous (3-5 seconds), ultra-low-cost cross-border payments and remittance settlement.",
            "Enterprise-grade XRP Ledger (XRPL) designed specifically for banks and central financial institutions.",
            "XRP functions as a bridge currency eliminating the need for pre-funded nostro/vostro accounts.",
            "High energy efficiency and deterministic consensus mechanism."
        ],
        "project_updates": [
            "Ripple USD (RLUSD) enterprise-grade stablecoin launch on XRPL and Ethereum.",
            "XRPL EVM sidechain developments allowing Ethereum smart contracts on the Ripple ledger.",
            "Expansion of Central Bank Digital Currency (CBDC) pilot partnerships worldwide."
        ],
        "future_scope": [
            "Value Outlook: Huge potential to capture portions of the trillion-dollar multi-currency cross-border payment market.",
            "Adoption Catalysts: Resolution of regulatory overhang, banking payment integration, and XRPL DeFi expansion.",
            "Key Risks: Competition from stablecoin payment networks and private bank ledgers."
        ]
    },
    "cardano": {
        "benefits": [
            "Peer-reviewed, evidence-based academic research design and Haskell-based formal verification.",
            "Extended UTXO (EUTXO) accounting model ensuring deterministic transaction execution and security.",
            "True decentralized liquid staking with zero lockup periods or slashing penalties.",
            "Strong focus on developing nations, identity management (Atala PRISM), and governance."
        ],
        "project_updates": [
            "Chang Hardfork entering the Voltaire era of full community governance and decentralized budgeting.",
            "Hydra layer-2 scaling protocol improving transaction bandwidth for decentralized applications.",
            "Midnight privacy sidechain development providing data protection for regulated applications."
        ],
        "future_scope": [
            "Value Outlook: Long-term value anchored in institutional resilience, governance stability, and academic-grade security.",
            "Adoption Catalysts: Voltaire decentralized governance maturity, real-world utility in Africa/Asia, and DeFi growth.",
            "Key Risks: Slower development pace relative to rapid consumer-focused chains."
        ]
    }
}

class AIAnalysisEngine:

    @classmethod
    def generate_coin_insights(cls, coin_data: Dict[str, Any], news_items: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Synthesizes market stats, news, benefits, project roadmap, and future scope.
        Uses Gemini AI if configured, otherwise leverages expert algorithmic synthesis.
        """
        coin_id = coin_data.get("id", "").lower()
        coin_name = coin_data.get("name", "")
        coin_symbol = coin_data.get("symbol", "")

        # Try Gemini AI first if API key is set
        if Config.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=Config.GEMINI_API_KEY)
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                news_summary_text = "\n".join([f"- {n['title']} (Source: {n['source']})" for n in news_items])
                
                prompt = f"""
You are a senior cryptocurrency analyst and blockchain researcher.
Analyze the following cryptocurrency:
Name: {coin_name} ({coin_symbol})
Current Price: ${coin_data.get('price_usd')} USD (₹{coin_data.get('price_inr')} INR)
24h Change: {coin_data.get('change_24h')}%
Market Cap Rank: #{coin_data.get('rank')}
Recent News:
{news_summary_text}

Provide an authoritative, clear breakdown for an investor/user in 4 concise sections:
1. MAJOR BENEFITS & REAL-WORLD UTILITY (3-4 bullet points highlighting core advantages, technology, problem solved)
2. CURRENT PROJECT & ECOSYSTEM UPDATES (2-3 bullet points on recent developments, upgrades, partnerships)
3. FUTURE SCOPE & VALUE OUTLOOK (2-3 bullet points on long-term growth potential, price catalysts, and key risks)
4. MARKET VERDICT & SENTIMENT (1 concise concluding summary)
"""
                response = model.generate_content(prompt)
                if response and response.text:
                    return {
                        "ai_generated": True,
                        "content": response.text.strip()
                    }
            except Exception as e:
                logger.warning(f"Gemini API generation fallback due to error: {e}")

        # Fallback / Built-in High Quality Synthesis Engine
        kb_entry = KNOWLEDGE_BASE.get(coin_id) or KNOWLEDGE_BASE.get(coin_symbol.lower())
        
        if kb_entry:
            benefits = kb_entry["benefits"]
            project_updates = kb_entry["project_updates"]
            future_scope = kb_entry["future_scope"]
        else:
            # Dynamic synthesis from metadata
            desc = coin_data.get("description_snippet", "")
            benefits = [
                f"Core Utility: {desc[:200]}..." if desc else f"{coin_name} offers a decentralized blockchain solution for fast digital transactions and ecosystem utility.",
                f"Market Presence: Ranked #{coin_data.get('rank', 'N/A')} by global market capitalization.",
                "Ecosystem: Decentralized protocol with open-source network participation."
            ]
            project_updates = [
                f"Active development and ecosystem transactions on the {coin_name} network.",
                f"Global liquidity available across major centralized and decentralized exchanges."
            ]
            future_scope = [
                f"Growth Potential: Dependent on broader crypto market adoption, utility expansion, and liquidity inflow.",
                f"Market Catalyst: Expansion of developer ecosystem and real-world adoption.",
                f"Risk Factors: Market volatility and broader regulatory environment."
            ]

        # Format into clean structured text
        insights_text = f"""
💡 *MAJOR BENEFITS & UTILITY*:
{chr(10).join(['• ' + b for b in benefits])}

🛠️ *PROJECT & ECOSYSTEM UPDATES*:
{chr(10).join(['• ' + p for p in project_updates])}

🚀 *FUTURE SCOPE & VALUE POTENTIAL*:
{chr(10).join(['• ' + f for f in future_scope])}
"""
        return {
            "ai_generated": False,
            "content": insights_text.strip(),
            "benefits": benefits,
            "project_updates": project_updates,
            "future_scope": future_scope
        }

    @classmethod
    def format_full_report_html(cls, coin_data: Dict[str, Any], news_items: List[Dict[str, str]], insights: Dict[str, Any]) -> str:
        """Formats the entire analysis nicely for Telegram (HTML mode)."""
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

        # Format large numbers
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

        # News list
        news_section = ""
        if news_items:
            news_section = "\n📰 <b>RECENT UPDATED NEWS & HEADLINES:</b>\n"
            for n in news_items[:3]:
                title = n['title'].replace("<", "&lt;").replace(">", "&gt;")
                news_section += f"• <a href='{n['link']}'>{title}</a> <i>({n['source']})</i>\n"
        else:
            news_section = "\n📰 <b>RECENT NEWS:</b> Market sentiment remains active.\n"

        insights_content = insights.get("content", "").replace("<", "&lt;").replace(">", "&gt;") if insights.get("ai_generated") else insights.get("content", "")

        msg = f"""🔥 <b>{name} ({sym}) MARKET & FUTURE SCOPE INTELLIGENCE</b> 🔥

📊 <b>CURRENT MARKET UPDATE:</b>
• <b>Price:</b> ${price_usd:,.4f} USD | ₹{price_inr:,.2f} INR
• <b>24h Change:</b> {trend_emoji} <b>{change_sign}{chg_24h}%</b>
• <b>24h Range:</b> ${low_24h:,.4f} - ${high_24h:,.4f}
• <b>Market Cap:</b> {format_currency(mcap)} (Rank #{rank})
• <b>All-Time High:</b> ${ath:,.2f} ({ath_change}%)
{news_section}
{insights_content}

⚡ <i>Sent via Crypto Intelligence Alert Engine</i>
"""
        return msg.strip()

    @classmethod
    def format_whatsapp_message(cls, coin_data: Dict[str, Any], news_items: List[Dict[str, str]], insights: Dict[str, Any]) -> str:
        """Formats the analysis using WhatsApp markdown (*bold*, _italic_)."""
        name = coin_data.get("name", "Crypto")
        sym = coin_data.get("symbol", "")
        price_usd = coin_data.get("price_usd", 0)
        price_inr = coin_data.get("price_inr", 0)
        chg_24h = coin_data.get("change_24h", 0)
        rank = coin_data.get("rank", "N/A")
        mcap = coin_data.get("market_cap_usd", 0)
        ath = coin_data.get("ath_usd", 0)
        high_24h = coin_data.get("high_24h", 0)
        low_24h = coin_data.get("low_24h", 0)

        trend_emoji = "🟢 📈" if chg_24h >= 0 else "🔴 📉"
        change_sign = "+" if chg_24h >= 0 else ""

        def format_currency(num):
            if num >= 1_000_000_000:
                return f"${num/1_000_000_000:.2f}B"
            elif num >= 1_000_000:
                return f"${num/1_000_000:.2f}M"
            elif num > 0:
                return f"${num:,.4f}"
            return "N/A"

        news_section = ""
        if news_items:
            news_section = "\n📰 *RECENT NEWS & HEADLINES:*\n"
            for n in news_items[:3]:
                news_section += f"• {n['title']} ({n['source']})\n"

        msg = f"""🔥 *{name} ({sym}) INTELLIGENCE REPORT* 🔥

📊 *CURRENT MARKET UPDATE:*
• Price: *${price_usd:,.4f} USD* (₹{price_inr:,.2f} INR)
• 24h Change: {trend_emoji} *{change_sign}{chg_24h}%*
• 24h Range: ${low_24h:,.4f} - ${high_24h:,.4f}
• Market Cap: {format_currency(mcap)} (Rank #{rank})
• All-Time High: ${ath:,.2f}
{news_section}
{insights.get('content', '')}

⚡ _Crypto Intelligence Bot_
"""
        return msg.strip()
