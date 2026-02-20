"""Policy announcements collector using crawlers."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.collectors.base import BaseCollector, DataPoint
from src.collectors.crawlers.pbc_crawler import PBCCrawler, PBCCNMarketCrawler
from src.collectors.crawlers.csrc_crawler import CSRCCrawler, NDCRCrawler


class PolicyCollector(BaseCollector):
    """Collector for official policy announcements from multiple sources."""

    def __init__(self, crawler_config: Dict[str, Any]):
        self.crawlers = []
        self._init_crawlers(crawler_config)

    def _init_crawlers(self, config: Dict[str, Any]):
        """Initialize crawlers based on configuration."""
        crawlers_config = config.get("crawlers", [])

        crawler_classes = {
            "pbc": PBCCrawler,
            "pbc_open_market": PBCCNMarketCrawler,
            "csrc": CSRCCrawler,
            "ndrc": NDCRCrawler,
        }

        for cfg in crawlers_config:
            if not cfg.get("enabled", True):
                continue

            crawler_type = cfg.get("type", "")
            crawler_class = crawler_classes.get(crawler_type)

            if crawler_class:
                self.crawlers.append(crawler_class())

        if not self.crawlers:
            self.crawlers = [
                PBCCrawler(),
                PBCCNMarketCrawler(),
                CSRCCrawler(),
                NDCRCrawler(),
            ]

    async def collect(self) -> List[DataPoint]:
        """Collect announcements from all crawlers."""
        results = []

        tasks = [crawler.fetch() for crawler in self.crawlers]
        all_items = await asyncio.gather(*tasks, return_exceptions=True)

        for crawler, items in zip(self.crawlers, all_items):
            if isinstance(items, Exception):
                print(f"[{crawler.name}] Error: {items}")
                continue

            for item in items:
                dp = DataPoint(
                    timestamp=item.get("timestamp", datetime.now()),
                    source=item.get("source", crawler.name),
                    data_type="policy_announcement",
                    content=item.get("content", {}),
                    metadata={
                        "category": item.get("category", ""),
                        "url": item.get("url", ""),
                    },
                )
                results.append(dp)

        return results

    async def collect_one(self, symbol: str) -> Optional[DataPoint]:
        """Not applicable for policy collector."""
        return None

    def format_for_llm(self, data: List[DataPoint]) -> str:
        """Format policy announcements for LLM analysis."""
        lines = ["## 政策公告\n"]

        if not data:
            lines.append("暂无最新政策公告")
            return "\n".join(lines)

        for dp in sorted(data, key=lambda x: x.timestamp, reverse=True)[:15]:
            content = dp.content
            title = content.get("title", "")
            source = dp.source
            date = content.get("published", "") or dp.timestamp.strftime("%m-%d %H:%M")

            if title:
                lines.append(f"- [{source}] {date}: {title}")

        return "\n".join(lines)

    def get_important_keywords(self, data: List[DataPoint]) -> Dict[str, int]:
        """Extract important policy keywords."""
        keywords: Dict[str, int] = {}

        important_keywords = [
            "降准",
            "降息",
            "加息",
            "利率",
            "货币政策",
            "公开市场",
            "MLF",
            "LPR",
            "IPO",
            "注册制",
            "减持",
            "再融资",
            "宏观调控",
            "产业政策",
            "经济数据",
            "房地产",
            "金融监管",
            "资本市场",
        ]

        for dp in data:
            title = dp.content.get("title", "")
            text = title.lower()

            for kw in important_keywords:
                if kw in text:
                    keywords[kw] = keywords.get(kw, 0) + 1

        return dict(sorted(keywords.items(), key=lambda x: x[1], reverse=True))
