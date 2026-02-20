"""WeChat Work (企业微信) notification channel."""

import httpx


class WeChatNotifier:
    name = "wechat"

    def __init__(self, webhook: str):
        self.webhook = webhook

    def send(self, message: str) -> bool:
        if not self.webhook:
            print("WeChat: Missing webhook URL")
            return False

        payload = {
            "msgtype": "markdown",
            "markdown": {"content": message},
        }

        try:
            with httpx.Client() as client:
                response = client.post(self.webhook, json=payload, timeout=10)
                data = response.json()
                return data.get("errcode", -1) == 0
        except Exception as e:
            print(f"WeChat error: {e}")
            return False

    async def send_async(self, message: str) -> bool:
        if not self.webhook:
            return False

        payload = {
            "msgtype": "markdown",
            "markdown": {"content": message},
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook, json=payload, timeout=10)
                data = response.json()
                return data.get("errcode", -1) == 0
        except Exception:
            return False

    def send_card(
        self,
        title: str,
        description: str,
        url: str,
        btntxt: str = "查看详情",
    ) -> bool:
        payload = {
            "msgtype": "template_card",
            "template_card": {
                "card_type": "text_notice",
                "main_title": {"title": title, "desc": description},
                "card_action": {
                    "type": 1,
                    "url": url,
                },
                "button_selection": {
                    "button_list": [{"text": btntxt}],
                },
            },
        }

        try:
            with httpx.Client() as client:
                response = client.post(self.webhook, json=payload, timeout=10)
                data = response.json()
                return data.get("errcode", -1) == 0
        except Exception:
            return False
