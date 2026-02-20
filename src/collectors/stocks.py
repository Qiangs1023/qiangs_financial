"""Stock data collector using AKShare and yfinance."""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional

import akshare as ak
import yfinance as yf

from src.collectors.base import BaseCollector, DataPoint


class StockCollector(BaseCollector):
    def __init__(self, stocks_config: List[Dict]):
        self.stocks = stocks_config
        self.cache: Dict[str, DataPoint] = {}

    async def collect(self) -> List[DataPoint]:
        results = []
        for stock in self.stocks:
            try:
                dp = await self.collect_one(stock["symbol"])
                if dp:
                    results.append(dp)
            except Exception as e:
                print(f"Error collecting {stock['symbol']}: {e}")
        return results

    async def collect_one(self, symbol: str) -> Optional[DataPoint]:
        stock_config = next((s for s in self.stocks if s["symbol"] == symbol), None)
        if not stock_config:
            return None

        market = stock_config.get("market", "a股")

        if market == "A股" or market == "a股":
            return await self._collect_china_stock(symbol)
        elif market == "美股":
            return await self._collect_us_stock(symbol)
        elif market == "港股":
            return await self._collect_hk_stock(symbol)
        else:
            return await self._collect_us_stock(symbol)

    async def _collect_china_stock(self, symbol: str) -> DataPoint:
        code = symbol.split(".")[0]

        def fetch():
            try:
                df = ak.stock_zh_a_spot_em()
                row = df[df["代码"] == code]
                if row.empty:
                    return None
                row = row.iloc[0]
                return {
                    "symbol": symbol,
                    "name": row.get("名称", ""),
                    "price": float(row.get("最新价", 0)),
                    "change_pct": float(row.get("涨跌幅", 0)),
                    "volume": float(row.get("成交量", 0)),
                    "amount": float(row.get("成交额", 0)),
                    "high": float(row.get("最高", 0)),
                    "low": float(row.get("最低", 0)),
                    "open": float(row.get("今开", 0)),
                    "prev_close": float(row.get("昨收", 0)),
                }
            except Exception:
                return None

        data = await asyncio.to_thread(fetch)

        return DataPoint(
            timestamp=datetime.now(),
            source="akshare",
            data_type="stock_realtime",
            content=data or {},
            metadata={"symbol": symbol, "market": "A股"},
        )

    async def _collect_us_stock(self, symbol: str) -> DataPoint:
        def fetch():
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period="2d")
                if hist.empty:
                    return None

                current = hist.iloc[-1]
                prev = hist.iloc[-2] if len(hist) > 1 else current
                change_pct = (
                    ((current["Close"] - prev["Close"]) / prev["Close"]) * 100
                    if len(hist) > 1
                    else 0
                )

                return {
                    "symbol": symbol,
                    "name": info.get("shortName", ""),
                    "price": float(current["Close"]),
                    "change_pct": round(change_pct, 2),
                    "volume": int(current["Volume"]),
                    "high": float(current["High"]),
                    "low": float(current["Low"]),
                    "open": float(current["Open"]),
                    "prev_close": float(prev["Close"]),
                    "market_cap": info.get("marketCap", 0),
                    "pe_ratio": info.get("trailingPE", 0),
                }
            except Exception:
                return None

        data = await asyncio.to_thread(fetch)

        return DataPoint(
            timestamp=datetime.now(),
            source="yfinance",
            data_type="stock_realtime",
            content=data or {},
            metadata={"symbol": symbol, "market": "美股"},
        )

    async def _collect_hk_stock(self, symbol: str) -> DataPoint:
        code = symbol.split(".")[0]

        def fetch():
            try:
                df = ak.stock_hk_spot_em()
                row = df[df["代码"] == code]
                if row.empty:
                    return None
                row = row.iloc[0]
                return {
                    "symbol": symbol,
                    "name": row.get("名称", ""),
                    "price": float(row.get("最新价", 0)),
                    "change_pct": float(row.get("涨跌幅", 0)),
                    "volume": float(row.get("成交量", 0)),
                    "high": float(row.get("最高", 0)),
                    "low": float(row.get("最低", 0)),
                }
            except Exception:
                return None

        data = await asyncio.to_thread(fetch)

        return DataPoint(
            timestamp=datetime.now(),
            source="akshare",
            data_type="stock_realtime",
            content=data or {},
            metadata={"symbol": symbol, "market": "港股"},
        )

    def get_market_summary(self, data: List[DataPoint]) -> Dict:
        if not data:
            return {"total": 0, "gainers": 0, "losers": 0}

        gainers = sum(1 for d in data if d.content.get("change_pct", 0) > 0)
        losers = sum(1 for d in data if d.content.get("change_pct", 0) < 0)

        return {
            "total": len(data),
            "gainers": gainers,
            "losers": losers,
            "unchanged": len(data) - gainers - losers,
        }
