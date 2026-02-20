"""Telegram notification channel."""

import os
from typing import Optional, List, Dict

import httpx


def get_proxy() -> Optional[str]:
    """Get proxy from environment variables."""
    return (
        os.getenv("HTTPS_PROXY")
        or os.getenv("https_proxy")
        or os.getenv("HTTP_PROXY")
        or os.getenv("http_proxy")
    )


class TelegramNotifier:
    name = "telegram"

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.proxy = get_proxy()

    def send(self, message: str) -> bool:
        if not self.bot_token or not self.chat_id:
            print("Telegram: Missing bot_token or chat_id")
            return False

        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }

        try:
            proxies = {"http://": self.proxy, "https://": self.proxy} if self.proxy else None
            with httpx.Client(proxy=self.proxy, timeout=30) as client:
                response = client.post(url, json=payload)
                return response.status_code == 200
        except Exception as e:
            print(f"Telegram error: {e}")
            return False

    async def send_async(self, message: str) -> bool:
        if not self.bot_token or not self.chat_id:
            return False

        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }

        try:
            async with httpx.AsyncClient(proxy=self.proxy, timeout=30) as client:
                response = await client.post(url, json=payload)
                return response.status_code == 200
        except Exception:
            return False

    def send_with_buttons(self, message: str, buttons: List[List[Dict]]) -> bool:
        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "reply_markup": {"inline_keyboard": buttons},
        }

        try:
            with httpx.Client(proxy=self.proxy, timeout=30) as client:
                response = client.post(url, json=payload)
                return response.status_code == 200
        except Exception:
            return False
