import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Common symbol to CoinGecko ID mapping for instant resolution
COMMON_MAP = {
    "btc": "bitcoin",
    "bitcoin": "bitcoin",
    "eth": "ethereum",
    "ethereum": "ethereum",
    "sol": "solana",
    "solana": "solana",
    "bnb": "binancecoin",
    "binance": "binancecoin",
    "xrp": "ripple",
    "ripple": "ripple",
    "ada": "cardano",
    "cardano": "cardano",
    "doge": "dogecoin",
    "dogecoin": "dogecoin",
    "dot": "polkadot",
    "polkadot": "polkadot",
    "matic": "matic-network",
    "polygon": "matic-network",
    "pol": "matic-network",
    "bdx": "beldex",
    "beldex": "beldex",
    "trx": "tron",
    "tron": "tron",
    "avax": "avalanche-2",
    "avalanche": "avalanche-2",
    "link": "chainlink",
    "chainlink": "chainlink",
    "shib": "shiba-inu",
    "near": "near",
    "sui": "sui",
    "apt": "aptos",
    "ton": "the-open-network",
    "toncoin": "the-open-network",
    "pepe": "pepe",
    "ltc": "litecoin",
    "litecoin": "litecoin",
    "bch": "bitcoin-cash",
    "monero": "monero",
    "xmr": "monero",
    "kas": "kaspa",
    "kaspa": "kaspa"
}

class CryptoMarketData:
    COINGECKO_BASE = "https://api.coingecko.com/api/v3"

    @classmethod
    def resolve_coin_id(cls, query: str) -> str:
        q_clean = query.strip().lower()
        if q_clean in COMMON_MAP:
            return COMMON_MAP[q_clean]
        
        # Search via CoinGecko Search API
        try:
            url = f"{cls.COINGECKO_BASE}/search?query={q_clean}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                coins = data.get("coins", [])
                if coins:
                    return coins[0]["id"]
        except Exception as e:
            logger.warning(f"CoinGecko search error for '{query}': {e}")

        return q_clean

    @classmethod
    def get_coin_overview(cls, coin_name_or_symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetches detailed real-time market data for the given coin.
        """
        coin_id = cls.resolve_coin_id(coin_name_or_symbol)

        try:
            url = f"{cls.COINGECKO_BASE}/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=true&developer_data=true&sparkline=false"
            resp = requests.get(url, timeout=12)
            
            if resp.status_code == 200:
                data = resp.json()
                md = data.get("market_data", {})
                
                current_price_usd = md.get("current_price", {}).get("usd", 0)
                current_price_inr = md.get("current_price", {}).get("inr", 0)
                price_change_24h = md.get("price_change_percentage_24h", 0) or 0
                price_change_7d = md.get("price_change_percentage_7d", 0) or 0
                price_change_30d = md.get("price_change_percentage_30d", 0) or 0
                
                market_cap_usd = md.get("market_cap", {}).get("usd", 0)
                market_cap_rank = data.get("market_cap_rank") or "N/A"
                
                total_volume_usd = md.get("total_volume", {}).get("usd", 0)
                high_24h_usd = md.get("high_24h", {}).get("usd", 0)
                low_24h_usd = md.get("low_24h", {}).get("usd", 0)
                
                ath_usd = md.get("ath", {}).get("usd", 0)
                ath_change_pct = md.get("ath_change_percentage", {}).get("usd", 0)
                ath_date = md.get("ath_date", {}).get("usd", "")[:10]
                
                circulating_supply = md.get("circulating_supply", 0)
                max_supply = md.get("max_supply") or md.get("total_supply")
                
                categories = data.get("categories", [])
                links = data.get("links", {})
                homepage = links.get("homepage", [""])[0] if links.get("homepage") else ""
                whitepaper = links.get("whitepaper", "")
                
                description_en = data.get("description", {}).get("en", "")
                # Clean up html tags in description if any
                if description_en:
                    import re
                    description_en = re.sub(r"<[^>]+>", "", description_en).strip()
                    # Keep first 500 chars for context
                    description_snippet = description_en[:600]
                else:
                    description_snippet = ""

                return {
                    "id": data.get("id", coin_id),
                    "name": data.get("name", coin_name_or_symbol.upper()),
                    "symbol": data.get("symbol", "").upper(),
                    "rank": market_cap_rank,
                    "price_usd": current_price_usd,
                    "price_inr": current_price_inr,
                    "change_24h": round(price_change_24h, 2),
                    "change_7d": round(price_change_7d, 2),
                    "change_30d": round(price_change_30d, 2),
                    "high_24h": high_24h_usd,
                    "low_24h": low_24h_usd,
                    "market_cap_usd": market_cap_usd,
                    "volume_24h_usd": total_volume_usd,
                    "ath_usd": ath_usd,
                    "ath_change_pct": round(ath_change_pct, 2) if ath_change_pct else 0,
                    "ath_date": ath_date,
                    "circulating_supply": circulating_supply,
                    "max_supply": max_supply,
                    "categories": categories[:3] if categories else [],
                    "homepage": homepage,
                    "whitepaper": whitepaper,
                    "description_snippet": description_snippet
                }

        except Exception as e:
            logger.error(f"Error fetching CoinGecko data for {coin_id}: {e}")

        # Fallback to simple price / Binance API if CoinGecko is rate limited
        return cls._fallback_binance(coin_name_or_symbol)

    @classmethod
    def _fallback_binance(cls, coin_name_or_symbol: str) -> Optional[Dict[str, Any]]:
        try:
            sym = coin_name_or_symbol.strip().upper()
            if sym in ["BITCOIN", "BTC"]:
                pair = "BTCUSDT"
                name, sym = "Bitcoin", "BTC"
            elif sym in ["ETHEREUM", "ETH"]:
                pair = "ETHUSDT"
                name, sym = "Ethereum", "ETH"
            elif sym in ["SOLANA", "SOL"]:
                pair = "SOLUSDT"
                name, sym = "Solana", "SOL"
            else:
                pair = f"{sym}USDT"
                name = sym

            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={pair}"
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                d = resp.json()
                price = float(d.get("lastPrice", 0))
                change_24h = float(d.get("priceChangePercent", 0))
                high_24h = float(d.get("highPrice", 0))
                low_24h = float(d.get("lowPrice", 0))
                vol_usd = float(d.get("quoteVolume", 0))

                return {
                    "id": sym.lower(),
                    "name": name,
                    "symbol": sym,
                    "rank": "Top 100",
                    "price_usd": price,
                    "price_inr": round(price * 87.5, 2),
                    "change_24h": round(change_24h, 2),
                    "change_7d": 0.0,
                    "change_30d": 0.0,
                    "high_24h": high_24h,
                    "low_24h": low_24h,
                    "market_cap_usd": 0,
                    "volume_24h_usd": vol_usd,
                    "ath_usd": 0,
                    "ath_change_pct": 0,
                    "ath_date": "",
                    "circulating_supply": 0,
                    "max_supply": None,
                    "categories": ["Cryptocurrency"],
                    "homepage": "",
                    "whitepaper": "",
                    "description_snippet": f"{name} ({sym}) cryptocurrency."
                }
        except Exception as e:
            logger.error(f"Binance fallback error: {e}")
        
        return None

    @classmethod
    def get_trending_coins(cls) -> list:
        """Fetches top trending coins on CoinGecko."""
        try:
            url = f"{cls.COINGECKO_BASE}/search/trending"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                coins = data.get("coins", [])
                trending_list = []
                for c in coins[:6]:
                    item = c.get("item", {})
                    trending_list.append({
                        "name": item.get("name"),
                        "symbol": item.get("symbol"),
                        "rank": item.get("market_cap_rank"),
                        "price_btc": item.get("price_btc"),
                        "thumb": item.get("thumb")
                    })
                return trending_list
        except Exception as e:
            logger.error(f"Error fetching trending coins: {e}")
        return []
