"""Notification dispatcher."""

from src.config import NotificationConfig
from src.notifier.telegram import TelegramNotifier
from src.notifier.wechat import WeChatNotifier


class NotificationDispatcher:
    def __init__(self, config: NotificationConfig):
        self.channels = []

        if config.telegram.enabled:
            self.channels.append(
                TelegramNotifier(
                    bot_token=config.telegram.bot_token,
                    chat_id=config.telegram.chat_id,
                )
            )

        if config.wechat.enabled:
            self.channels.append(WeChatNotifier(webhook=config.wechat.webhook))

    def send_all(self, message: str) -> dict[str, dict]:
        results = {}
        for channel in self.channels:
            try:
                success = channel.send(message)
                results[channel.name] = {
                    "success": success,
                    "message": "OK" if success else "Failed",
                }
            except Exception as e:
                results[channel.name] = {
                    "success": False,
                    "message": str(e),
                }
        return results

    async def send_all_async(self, message: str) -> dict[str, dict]:
        import asyncio

        results = {}
        tasks = []
        for channel in self.channels:
            tasks.append((channel.name, channel.send_async(message)))

        for name, task in tasks:
            try:
                success = await task
                results[name] = {"success": success, "message": "OK"}
            except Exception as e:
                results[name] = {"success": False, "message": str(e)}

        return results
