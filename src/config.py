"""Configuration management using Pydantic."""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

load_dotenv()


class StockConfig(BaseModel):
    symbol: str
    name: Optional[str] = None
    market: str = "a股"


class CryptoConfig(BaseModel):
    symbol: str
    exchange: str = "binance"


class RSSSource(BaseModel):
    name: str
    url: str
    category: str = "general"


class TwitterConfig(BaseModel):
    enabled: bool = False
    accounts: List[str] = []
    bearer_token: str = ""


class NewsConfig(BaseModel):
    rss: List[RSSSource] = []
    twitter: TwitterConfig = TwitterConfig()


class LLMConfig(BaseModel):
    provider: str = "deepseek"
    model: str = "deepseek-chat"
    temperature: float = 0.3
    api_key: str = ""
    base_url: str = "https://api.deepseek.com"


class TelegramConfig(BaseModel):
    enabled: bool = False
    bot_token: str = ""
    chat_id: str = ""


class WeChatConfig(BaseModel):
    enabled: bool = False
    webhook: str = ""


class NotificationConfig(BaseModel):
    telegram: TelegramConfig = TelegramConfig()
    wechat: WeChatConfig = WeChatConfig()


class ScheduleTask(BaseModel):
    enabled: bool = True
    cron: str = "0 * * * *"


class SchedulerConfig(BaseModel):
    market_snapshot: ScheduleTask = ScheduleTask()
    daily_report: ScheduleTask = ScheduleTask(cron="0 8 * * 1-5")
    anomaly_alert: ScheduleTask = ScheduleTask(cron="*/5 * * * *")


class AlertConfig(BaseModel):
    price_change_percent: float = 3.0
    volume_multiplier: float = 2.0


class MarketConfig(BaseModel):
    stocks: List[StockConfig] = []
    crypto: List[CryptoConfig] = []


class Config(BaseModel):
    markets: MarketConfig = MarketConfig()
    news: NewsConfig = NewsConfig()
    llm: LLMConfig = LLMConfig()
    notifications: NotificationConfig = NotificationConfig()
    scheduler: SchedulerConfig = SchedulerConfig()
    alerts: AlertConfig = AlertConfig()


class Settings(BaseSettings):
    config_path: Path = Field(default=Path("config.yaml"), alias="FINPULSE_CONFIG")

    def load_config(self) -> Config:
        if not self.config_path.exists():
            return Config()
        with open(self.config_path) as f:
            data = yaml.safe_load(f) or {}
        return self._substitute_env(data)

    def _substitute_env(self, data: Dict[str, Any]) -> Config:
        def replace_env(value: Any) -> Any:
            if isinstance(value, str):
                pattern = r"\$\{([^}]+)\}"
                matches = re.findall(pattern, value)
                for match in matches:
                    env_value = os.getenv(match, "")
                    value = value.replace(f"${{{match}}}", env_value)
                return value
            elif isinstance(value, dict):
                return {k: replace_env(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [replace_env(item) for item in value]
            return value

        result = replace_env(data)
        return Config(**result)


settings = Settings()
config = settings.load_config()
