"""Base crawler for policy announcements."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx


class BaseCrawler(ABC):
    """Abstract base class for web crawlers."""

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url
        self.cache: Dict[str, datetime] = {}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    @abstractmethod
    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch announcements from source."""
        pass

    @abstractmethod
    def parse(self, html: str) -> List[Dict[str, Any]]:
        """Parse HTML content and extract announcements."""
        pass

    async def get_html(self, url: Optional[str] = None) -> str:
        """Get HTML content from URL."""
        target_url = url or self.url
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                response = await client.get(target_url, headers=self.headers)
                response.encoding = response.encoding or "utf-8"
                return response.text
        except Exception as e:
            print(f"[{self.name}] Fetch error: {e}")
            return ""

    async def get_latest(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get latest announcements."""
        items = await self.fetch()
        return items[:count]

    def filter_new(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out already seen items."""
        new_items = []
        for item in items:
            item_id = item.get("url", "") or item.get("title", "")
            if item_id and item_id not in self.cache:
                self.cache[item_id] = datetime.now()
                new_items.append(item)
        return new_items

    def clear_old_cache(self, hours: int = 24):
        """Clear cache entries older than specified hours."""
        cutoff = datetime.now()
        keys_to_remove = [
            k for k, v in self.cache.items() if (cutoff - v).total_seconds() > hours * 3600
        ]
        for k in keys_to_remove:
            del self.cache[k]
