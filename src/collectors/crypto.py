"""Cryptocurrency data collector using CCXT."""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional

import ccxt.async_support as ccxt

from src.collectors.base import BaseCollector, DataPoint


class CryptoCollector(BaseCollector):
    def __init__(self, crypto_config: List[Dict]):
        self.symbols = crypto_config
        self.exchanges: Dict[str, ccxt.Exchange] = {}

    async def _get_exchange(self, name: str) -> ccxt.Exchange:
        if name not in self.exchanges:
            exchange_class = getattr(ccxt, name, None)
            if exchange_class:
                self.exchanges[name] = exchange_class({"enableRateLimit": True})
        return self.exchanges.get(name)

    async def collect(self) -> List[DataPoint]:
        results = []
        for symbol_config in self.symbols:
            try:
                dp = await self.collect_one(symbol_config["symbol"])
                if dp:
                    results.append(dp)
            except Exception as e:
                print(f"Error collecting {symbol_config['symbol']}: {e}")
        return results

    async def collect_one(self, symbol: str) -> Optional[DataPoint]:
        symbol_config = next((s for s in self.symbols if s["symbol"] == symbol), None)
        if not symbol_config:
            return None

        exchange_name = symbol_config.get("exchange", "binance")
        exchange = await self._get_exchange(exchange_name)

        if not exchange:
            return None

        try:
            ticker = await exchange.fetch_ticker(symbol)
            data = {
                "symbol": symbol,
                "price": ticker["last"],
                "change_pct": ticker.get("percentage", 0),
                "volume": ticker.get("baseVolume", 0),
                "quote_volume": ticker.get("quoteVolume", 0),
                "high": ticker.get("high", 0),
                "low": ticker.get("low", 0),
                "bid": ticker.get("bid", 0),
                "ask": ticker.get("ask", 0),
            }

            return DataPoint(
                timestamp=datetime.now(),
                source=exchange_name,
                data_type="crypto_realtime",
                content=data,
                metadata={"symbol": symbol, "exchange": exchange_name},
            )
        except Exception:
            return None

    async def close(self):
        for exchange in self.exchanges.values():
            await exchange.close()
        self.exchanges.clear()

    def format_for_llm(self, data: List[DataPoint]) -> str:
        lines = ["Cryptocurrency Market Data:"]
        for dp in data:
            c = dp.content
            change_emoji = "📈" if c.get("change_pct", 0) > 0 else "📉"
            lines.append(
                f"  {c['symbol']}: ${c['price']:,.2f} {change_emoji} {c['change_pct']:.2f}% "
                f"(Vol: ${c.get('quote_volume', 0):,.0f})"
            )
        return "\n".join(lines)
