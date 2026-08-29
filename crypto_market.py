import logging
import requests
import time
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# In-memory cache for instant responses (<10ms)
_MARKET_CACHE: Dict[str, Any] = {}
CACHE_TTL_SECONDS = 60

# Mapping of common coin queries to CoinPaprika IDs and details
PAPRIKA_MAP = {
    "btc": "btc-bitcoin",
    "bitcoin": "btc-bitcoin",
    "eth": "eth-ethereum",
    "ethereum": "eth-ethereum",
    "sol": "sol-solana",
    "solana": "sol-solana",
    "bdx": "bdx-beldex",
    "beldex": "bdx-beldex",
    "xrp": "xrp-xrp",
    "ripple": "xrp-xrp",
    "ada": "ada-cardano",
    "cardano": "ada-cardano",
    "doge": "doge-dogecoin",
    "dogecoin": "doge-dogecoin",
    "bnb": "bnb-binance-coin",
    "binance": "bnb-binance-coin",
    "dot": "dot-polkadot",
    "polkadot": "dot-polkadot",
    "matic": "matic-polygon",
    "polygon": "matic-polygon",
    "pol": "matic-polygon",
    "trx": "trx-tron",
    "tron": "trx-tron",
    "avax": "avax-avalanche",
    "avalanche": "avax-avalanche",
    "link": "link-chainlink",
    "chainlink": "link-chainlink",
    "shib": "shib-shiba-inu",
    "near": "near-near-protocol",
    "sui": "sui-sui",
    "ton": "ton-toncoin",
    "toncoin": "ton-toncoin",
    "pepe": "pepe-pepe",
    "ltc": "ltc-litecoin",
    "litecoin": "ltc-litecoin",
    "monero": "xmr-monero",
    "xmr": "xmr-monero",
    "kas": "kas-kaspa",
    "kaspa": "kas-kaspa"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

class CryptoMarketData:

    @classmethod
    def get_coin_overview(cls, coin_name_or_symbol: str) -> Optional[Dict[str, Any]]:
        q_clean = coin_name_or_symbol.strip().lower()

        # Check Cache
        now = time.time()
        if q_clean in _MARKET_CACHE:
            cached_time, cached_data = _MARKET_CACHE[q_clean]
            if now - cached_time < CACHE_TTL_SECONDS:
                return cached_data

        # Tier 1: CoinPaprika API (Ultra-reliable on Cloud)
        res = cls._fetch_paprika(q_clean)
        if res:
            _MARKET_CACHE[q_clean] = (now, res)
            _MARKET_CACHE[res['symbol'].lower()] = (now, res)
            _MARKET_CACHE[res['name'].lower()] = (now, res)
            return res

        # Tier 2: CoinGecko API (with custom browser headers)
        res_cg = cls._fetch_coingecko(q_clean)
        if res_cg:
            _MARKET_CACHE[q_clean] = (now, res_cg)
            return res_cg

        # Tier 3: Binance API
        res_binance = cls._fetch_binance(q_clean)
        if res_binance:
            _MARKET_CACHE[q_clean] = (now, res_binance)
            return res_binance

        return None

    @classmethod
    def _fetch_paprika(cls, query: str) -> Optional[Dict[str, Any]]:
        try:
            paprika_id = PAPRIKA_MAP.get(query)
            if not paprika_id:
                # Search on CoinPaprika
                s_url = f"https://api.coinpaprika.com/v1/search?q={query}&c=currencies"
                s_resp = requests.get(s_url, headers=HEADERS, timeout=4)
                if s_resp.status_code == 200:
                    currencies = s_resp.json().get("currencies", [])
                    if currencies:
                        paprika_id = currencies[0]["id"]

            if not paprika_id:
                paprika_id = f"{query}-{query}"

            url = f"https://api.coinpaprika.com/v1/tickers/{paprika_id}"
            resp = requests.get(url, headers=HEADERS, timeout=5)
            if resp.status_code == 200:
                d = resp.json()
                quotes = d.get("quotes", {}).get("USD", {})
                price_usd = quotes.get("price", 0)
                price_inr = round(price_usd * 87.5, 2)
                change_24h = quotes.get("percent_change_24h", 0) or 0
                change_7d = quotes.get("percent_change_7d", 0) or 0
                market_cap = quotes.get("market_cap", 0)
                volume_24h = quotes.get("volume_24h", 0)
                ath_usd = quotes.get("ath_price", 0) or 0
                ath_pct = quotes.get("percent_from_price_ath", 0) or 0
                rank = d.get("rank", "N/A")

                # Fetch 24h high/low estimate or approximate range
                high_24h = price_usd * (1 + abs(change_24h)/200)
                low_24h = price_usd * (1 - abs(change_24h)/200)

                return {
                    "id": d.get("id", query),
                    "name": d.get("name", query.capitalize()),
                    "symbol": d.get("symbol", query.upper()),
                    "rank": rank,
                    "price_usd": price_usd,
                    "price_inr": price_inr,
                    "change_24h": round(change_24h, 2),
                    "change_7d": round(change_7d, 2),
                    "high_24h": high_24h,
                    "low_24h": low_24h,
                    "market_cap_usd": market_cap,
                    "volume_24h_usd": volume_24h,
                    "ath_usd": ath_usd,
                    "ath_change_pct": round(ath_pct, 2),
                    "description_snippet": f"{d.get('name')} ({d.get('symbol')}) is a decentralized cryptocurrency."
                }
        except Exception as e:
            logger.warning(f"CoinPaprika fetch failed for '{query}': {e}")
        return None

    @classmethod
    def _fetch_coingecko(cls, query: str) -> Optional[Dict[str, Any]]:
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{query}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false"
            resp = requests.get(url, headers=HEADERS, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                md = data.get("market_data", {})
                price_usd = md.get("current_price", {}).get("usd", 0)
                price_inr = md.get("current_price", {}).get("inr", 0)
                change_24h = md.get("price_change_percentage_24h", 0) or 0
                return {
                    "id": data.get("id", query),
                    "name": data.get("name", query.capitalize()),
                    "symbol": data.get("symbol", query.upper()).upper(),
                    "rank": data.get("market_cap_rank", "N/A"),
                    "price_usd": price_usd,
                    "price_inr": price_inr,
                    "change_24h": round(change_24h, 2),
                    "change_7d": round(md.get("price_change_percentage_7d", 0) or 0, 2),
                    "high_24h": md.get("high_24h", {}).get("usd", 0),
                    "low_24h": md.get("low_24h", {}).get("usd", 0),
                    "market_cap_usd": md.get("market_cap", {}).get("usd", 0),
                    "volume_24h_usd": md.get("total_volume", {}).get("usd", 0),
                    "ath_usd": md.get("ath", {}).get("usd", 0),
                    "ath_change_pct": round(md.get("ath_change_percentage", {}).get("usd", 0) or 0, 2),
                    "description_snippet": f"{data.get('name')} cryptocurrency."
                }
        except Exception:
            pass
        return None

    @classmethod
    def _fetch_binance(cls, query: str) -> Optional[Dict[str, Any]]:
        try:
            sym = query.upper()
            pair = f"{sym}USDT"
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={pair}"
            resp = requests.get(url, headers=HEADERS, timeout=4)
            if resp.status_code == 200:
                d = resp.json()
                price = float(d.get("lastPrice", 0))
                change_24h = float(d.get("priceChangePercent", 0))
                return {
                    "id": sym.lower(),
                    "name": sym,
                    "symbol": sym,
                    "rank": "Top 100",
                    "price_usd": price,
                    "price_inr": round(price * 87.5, 2),
                    "change_24h": round(change_24h, 2),
                    "change_7d": 0.0,
                    "high_24h": float(d.get("highPrice", 0)),
                    "low_24h": float(d.get("lowPrice", 0)),
                    "market_cap_usd": 0,
                    "volume_24h_usd": float(d.get("quoteVolume", 0)),
                    "ath_usd": 0,
                    "ath_change_pct": 0,
                    "description_snippet": f"{sym} cryptocurrency."
                }
        except Exception:
            pass
        return None

    @classmethod
    def get_trending_coins(cls) -> list:
        try:
            url = "https://api.coinpaprika.com/v1/coins"
            resp = requests.get(url, headers=HEADERS, timeout=5)
            if resp.status_code == 200:
                coins = resp.json()[:6]
                return [{"name": c["name"], "symbol": c["symbol"], "rank": c["rank"]} for c in coins]
        except Exception:
            pass
        return [
            {"name": "Bitcoin", "symbol": "BTC", "rank": 1},
            {"name": "Ethereum", "symbol": "ETH", "rank": 2},
            {"name": "Solana", "symbol": "SOL", "rank": 5},
            {"name": "Beldex", "symbol": "BDX", "rank": 90}
        ]
