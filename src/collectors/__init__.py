"""Data collectors package."""

from src.collectors.base import BaseCollector, DataPoint
from src.collectors.crypto import CryptoCollector
from src.collectors.news import NewsCollector
from src.collectors.stocks import StockCollector
from src.collectors.policy_collector import PolicyCollector

__all__ = [
    "BaseCollector",
    "DataPoint",
    "StockCollector",
    "CryptoCollector",
    "NewsCollector",
    "PolicyCollector",
]
