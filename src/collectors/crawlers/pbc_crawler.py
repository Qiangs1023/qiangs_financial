"""People's Bank of China (PBC) announcement crawler."""

import re
from datetime import datetime
from typing import Any, Dict, List

from bs4 import BeautifulSoup

from .base_crawler import BaseCrawler


class PBCCrawler(BaseCrawler):
    """Crawler for PBC (央行) announcements.

    抓取中国人民银行货币政策、公开市场操作等公告。
    """

    def __init__(self):
        super().__init__(
            name="央行公告", url="http://www.pbc.gov.cn/zhengcehuobisi/125147/125153/index.html"
        )

    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch PBC announcements."""
        html = await self.get_html()
        if not html:
            return []

        items = self.parse(html)
        return self.filter_new(items)

    def parse(self, html: str) -> List[Dict[str, Any]]:
        """Parse PBC announcement page."""
        results = []

        try:
            soup = BeautifulSoup(html, "html.parser")

            items = soup.select("ul.list li a, div.newslist a, table a")

            for item in items[:20]:
                title = item.get_text(strip=True)
                if not title:
                    continue

                href = item.get("href", "")
                if href:
                    if href.startswith("/"):
                        url = f"http://www.pbc.gov.cn{href}"
                    elif href.startswith("./"):
                        url = self.url.rsplit("/", 1)[0] + "/" + href[2:]
                    else:
                        url = href
                else:
                    continue

                parent = item.parent
                date_str = ""
                if parent:
                    date_match = re.search(
                        r"(\d{4}-\d{2}-\d{2}|\d{4}/\d{2}/\d{2})", parent.get_text()
                    )
                    if date_match:
                        date_str = date_match.group(1)

                results.append(
                    {
                        "title": title,
                        "url": url,
                        "source": self.name,
                        "category": "货币政策",
                        "published": date_str,
                        "timestamp": datetime.now(),
                        "content": {
                            "title": title,
                            "link": url,
                            "summary": "",
                            "published": date_str,
                        },
                    }
                )

        except Exception as e:
            print(f"[{self.name}] Parse error: {e}")

        return results


class PBCCNMarketCrawler(BaseCrawler):
    """Crawler for PBC open market operations (公开市场操作)."""

    def __init__(self):
        super().__init__(
            name="公开市场操作", url="http://www.pbc.gov.cn/zhengcehuobisi/125147/125151/index.html"
        )

    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch open market operation announcements."""
        html = await self.get_html()
        if not html:
            return []

        items = self.parse(html)
        return self.filter_new(items)

    def parse(self, html: str) -> List[Dict[str, Any]]:
        """Parse open market operation page."""
        results = []

        try:
            soup = BeautifulSoup(html, "html.parser")

            items = soup.select("ul.list li a, div.newslist a")

            for item in items[:10]:
                title = item.get_text(strip=True)
                if not title or "公开市场" not in title:
                    continue

                href = item.get("href", "")
                if href:
                    if href.startswith("/"):
                        url = f"http://www.pbc.gov.cn{href}"
                    else:
                        url = href
                else:
                    continue

                results.append(
                    {
                        "title": title,
                        "url": url,
                        "source": self.name,
                        "category": "公开市场",
                        "timestamp": datetime.now(),
                        "content": {
                            "title": title,
                            "link": url,
                            "summary": "",
                        },
                    }
                )

        except Exception as e:
            print(f"[{self.name}] Parse error: {e}")

        return results
