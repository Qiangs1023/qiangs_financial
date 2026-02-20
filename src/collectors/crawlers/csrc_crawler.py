"""China Securities Regulatory Commission (CSRC) announcement crawler."""

import re
from datetime import datetime
from typing import Any, Dict, List

from bs4 import BeautifulSoup

from .base_crawler import BaseCrawler


class CSRCCrawler(BaseCrawler):
    """Crawler for CSRC (证监会) announcements.

    抓取证监会政策法规、监管公告等。
    """

    def __init__(self):
        super().__init__(
            name="证监会公告", url="http://www.csrc.gov.cn/csrc/c100028/common_list.shtml"
        )

    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch CSRC announcements."""
        html = await self.get_html()
        if not html:
            return []

        items = self.parse(html)
        return self.filter_new(items)

    def parse(self, html: str) -> List[Dict[str, Any]]:
        """Parse CSRC announcement page."""
        results = []

        try:
            soup = BeautifulSoup(html, "html.parser")

            items = soup.select("ul.list li a, div.list a, table a")

            for item in items[:20]:
                title = item.get_text(strip=True)
                if not title:
                    continue

                href = item.get("href", "")
                if href:
                    if href.startswith("/"):
                        url = f"http://www.csrc.gov.cn{href}"
                    elif href.startswith("./") or href.startswith("../"):
                        url = f"http://www.csrc.gov.cn/csrc/c100028/{href}"
                    else:
                        url = href
                else:
                    continue

                parent = item.parent
                date_str = ""
                if parent:
                    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", parent.get_text())
                    if date_match:
                        date_str = date_match.group(1)

                results.append(
                    {
                        "title": title,
                        "url": url,
                        "source": self.name,
                        "category": "监管政策",
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


class CSRCIpoCrawler(BaseCrawler):
    """Crawler for IPO announcements."""

    def __init__(self):
        super().__init__(
            name="IPO审核", url="http://www.csrc.gov.cn/csrc/c100028/common_list.shtml"
        )

    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch IPO announcements."""
        html = await self.get_html()
        if not html:
            return []

        items = self.parse(html)
        return self.filter_new(items)

    def parse(self, html: str) -> List[Dict[str, Any]]:
        """Parse IPO announcements."""
        results = []

        try:
            soup = BeautifulSoup(html, "html.parser")

            items = soup.select("ul.list li a, div.list a")

            for item in items[:10]:
                title = item.get_text(strip=True)
                if not title:
                    continue

                keywords = ["IPO", "上市", "发行", "审核", "注册"]
                if not any(kw in title for kw in keywords):
                    continue

                href = item.get("href", "")
                if href:
                    if href.startswith("/"):
                        url = f"http://www.csrc.gov.cn{href}"
                    else:
                        url = href
                else:
                    continue

                results.append(
                    {
                        "title": title,
                        "url": url,
                        "source": self.name,
                        "category": "IPO",
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


class NDCRCrawler(BaseCrawler):
    """Crawler for NDRC (发改委) announcements.

    抓取发改委宏观经济政策、产业政策等。
    """

    def __init__(self):
        super().__init__(name="发改委公告", url="https://www.ndrc.gov.cn/xxgk/zcfb/index.html")

    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch NDRC announcements."""
        html = await self.get_html()
        if not html:
            return []

        items = self.parse(html)
        return self.filter_new(items)

    def parse(self, html: str) -> List[Dict[str, Any]]:
        """Parse NDRC announcement page."""
        results = []

        try:
            soup = BeautifulSoup(html, "html.parser")

            items = soup.select("ul.list li a, div.file-list a")

            for item in items[:15]:
                title = item.get_text(strip=True)
                if not title:
                    continue

                href = item.get("href", "")
                if href:
                    if href.startswith("/"):
                        url = f"https://www.ndrc.gov.cn{href}"
                    else:
                        url = href
                else:
                    continue

                results.append(
                    {
                        "title": title,
                        "url": url,
                        "source": self.name,
                        "category": "宏观政策",
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
