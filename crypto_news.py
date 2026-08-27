import logging
import requests
import feedparser
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class CryptoNewsFetcher:
    RSS_FEEDS = {
        "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "cointelegraph": "https://cointelegraph.com/rss",
        "decrypt": "https://decrypt.co/feed"
    }

    @classmethod
    def get_news_for_coin(cls, coin_name: str, coin_symbol: str, limit: int = 4) -> List[Dict[str, str]]:
        """
        Fetches latest news specifically mentioning the coin from multiple RSS feeds + Google News RSS.
        """
        news_items: List[Dict[str, str]] = []
        name_lower = coin_name.lower()
        sym_lower = coin_symbol.lower()

        # 1. Google News RSS for precise coin news
        try:
            query = f"{coin_name} cryptocurrency"
            gnews_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"
            feed = feedparser.parse(gnews_url)
            for entry in feed.entries[:limit]:
                news_items.append({
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.get("published", "")[:16],
                    "source": entry.get("source", {}).get("title", "Google News")
                })
        except Exception as e:
            logger.warning(f"Google News RSS error: {e}")

        # 2. General crypto feeds if needed
        if len(news_items) < limit:
            for source, feed_url in cls.RSS_FEEDS.items():
                try:
                    feed = feedparser.parse(feed_url)
                    for entry in feed.entries:
                        title_lower = entry.title.lower()
                        summary_lower = entry.get("summary", "").lower()
                        if name_lower in title_lower or sym_lower in title_lower or name_lower in summary_lower:
                            # Avoid duplicates
                            if not any(item["title"] == entry.title for item in news_items):
                                news_items.append({
                                    "title": entry.title,
                                    "link": entry.link,
                                    "published": entry.get("published", "")[:16],
                                    "source": source.capitalize()
                                })
                        if len(news_items) >= limit:
                            break
                except Exception as e:
                    logger.warning(f"RSS fetch error from {source}: {e}")

        return news_items[:limit]

    @classmethod
    def get_market_headlines(cls, limit: int = 5) -> List[Dict[str, str]]:
        """Fetches general top crypto market breaking headlines."""
        headlines: List[Dict[str, str]] = []
        try:
            feed = feedparser.parse("https://cointelegraph.com/rss")
            for entry in feed.entries[:limit]:
                headlines.append({
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.get("published", "")[:16],
                    "source": "CoinTelegraph"
                })
        except Exception as e:
            logger.error(f"Error fetching top headlines: {e}")
        return headlines
