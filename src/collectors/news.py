"""News and policy data collector from RSS feeds."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import urlparse

import feedparser

from src.collectors.base import BaseCollector, DataPoint


class NewsCollector(BaseCollector):
    def __init__(self, news_config: Dict):
        self.rss_feeds = news_config.get("rss", [])
        self.cache: Dict[str, datetime] = {}
        self.max_age_hours = 24

    async def collect(self) -> List[DataPoint]:
        results = []
        for feed in self.rss_feeds:
            try:
                items = await self._fetch_rss(feed)
                results.extend(items)
            except Exception as e:
                print(f"Error fetching {feed.get('name', feed.get('url'))}: {e}")
        return results

    async def collect_one(self, symbol: str) -> Optional[DataPoint]:
        return None

    async def _fetch_rss(self, feed_config: Dict) -> List[DataPoint]:
        url = feed_config.get("url")
        name = feed_config.get("name", urlparse(url).netloc)
        category = feed_config.get("category", "general")

        def fetch():
            return feedparser.parse(url)

        parsed = await asyncio.to_thread(fetch)

        results = []
        cutoff = datetime.now() - timedelta(hours=self.max_age_hours)

        for entry in parsed.entries[:20]:
            pub_date = self._parse_date(entry.get("published_parsed"))

            if pub_date and pub_date < cutoff:
                continue

            content = {
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", "")[:500],
                "published": pub_date.isoformat() if pub_date else "",
            }

            results.append(
                DataPoint(
                    timestamp=pub_date or datetime.now(),
                    source=name,
                    data_type="news",
                    content=content,
                    metadata={"category": category, "url": url},
                )
            )

        return results

    def _parse_date(self, time_tuple) -> Optional[datetime]:
        if not time_tuple:
            return None
        try:
            return datetime(*time_tuple[:6])
        except Exception:
            return None

    def format_for_llm(self, data: List[DataPoint]) -> str:
        lines = ["Recent News Headlines:"]
        seen = set()

        for dp in sorted(data, key=lambda x: x.timestamp, reverse=True)[:30]:
            title = dp.content.get("title", "")
            if title in seen:
                continue
            seen.add(title)

            source = dp.source
            time_str = dp.timestamp.strftime("%m-%d %H:%M") if dp.timestamp else ""
            lines.append(f"  [{source}] {time_str}: {title}")

        return "\n".join(lines)

    def get_keywords_trends(self, data: List[DataPoint]) -> Dict[str, int]:
        keywords: Dict[str, int] = {}

        important_keywords = [
            "降息",
            "加息",
            "利率",
            "央行",
            "通胀",
            "GDP",
            "贸易",
            "关税",
            "政策",
            "监管",
            "证监会",
            "美联储",
            "Fed",
            "利率决议",
            "经济数据",
            "就业",
            "PMI",
            "CPI",
            "PPI",
        ]

        for dp in data:
            title = dp.content.get("title", "").lower()
            summary = dp.content.get("summary", "").lower()
            text = title + " " + summary

            for kw in important_keywords:
                if kw.lower() in text:
                    keywords[kw] = keywords.get(kw, 0) + 1

        return dict(sorted(keywords.items(), key=lambda x: x[1], reverse=True))
