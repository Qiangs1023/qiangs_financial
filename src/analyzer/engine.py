"""LLM-powered market analysis engine."""

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List

from openai import AsyncOpenAI

from src.collectors import CryptoCollector, NewsCollector, StockCollector
from src.config import Config


class MarketAnalyzer:
    def __init__(self, config: Config):
        self.config = config
        self.stock_collector = StockCollector([s.model_dump() for s in config.markets.stocks])
        self.crypto_collector = CryptoCollector([c.model_dump() for c in config.markets.crypto])
        self.news_collector = NewsCollector(config.news.model_dump())
        self._init_llm_client()

    def _init_llm_client(self):
        llm_config = self.config.llm
        api_key = llm_config.api_key or os.getenv("DEEPSEEK_API_KEY", "")

        if llm_config.provider == "deepseek":
            self.llm_client = AsyncOpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com",
            )
            self.llm_model = llm_config.model or "deepseek-chat"
        elif llm_config.provider == "openai":
            self.llm_client = AsyncOpenAI(
                api_key=api_key or os.getenv("OPENAI_API_KEY", ""),
            )
            self.llm_model = llm_config.model or "gpt-4o"
        else:
            self.llm_client = AsyncOpenAI(
                api_key=api_key,
                base_url=llm_config.base_url,
            )
            self.llm_model = llm_config.model

        self.llm_temperature = llm_config.temperature

    async def collect_all_data(self, market: str = "all") -> Dict[str, Any]:
        results = {}

        tasks = []

        if market in ["all", "a股", "美股", "港股", "stocks"]:
            tasks.append(("stocks", self.stock_collector.collect()))
        if market in ["all", "crypto"]:
            tasks.append(("crypto", self.crypto_collector.collect()))
        if market in ["all", "news"]:
            tasks.append(("news", self.news_collector.collect()))

        for name, coro in tasks:
            try:
                results[name] = await coro
            except Exception as e:
                print(f"Error collecting {name}: {e}")
                results[name] = []

        return results

    async def analyze(self, market: str = "all") -> Dict[str, Any]:
        data = await self.collect_all_data(market)

        stocks = data.get("stocks", [])
        crypto = data.get("crypto", [])
        news = data.get("news", [])

        stock_data = self.stock_collector.format_for_llm(stocks)
        crypto_data = self.crypto_collector.format_for_llm(crypto)
        news_data = self.news_collector.format_for_llm(news)
        keywords = self.news_collector.get_keywords_trends(news)

        prompt = self._build_analysis_prompt(stock_data, crypto_data, news_data, keywords)

        report = await self._generate_report(prompt)

        return {
            "timestamp": datetime.now().isoformat(),
            "summary": self._generate_summary(stocks, crypto, keywords),
            "report": report,
            "data": {
                "stocks": [dp.content for dp in stocks],
                "crypto": [dp.content for dp in crypto],
                "news_keywords": keywords,
            },
        }

    def _build_analysis_prompt(
        self, stock_data: str, crypto_data: str, news_data: str, keywords: dict
    ) -> str:
        return f"""你是一个专业的金融市场分析师。请基于以下数据进行分析，预测市场波动趋势。

## 股票市场数据
{stock_data}

## 加密货币市场数据
{crypto_data}

## 最新财经新闻
{news_data}

## 新闻关键词趋势
{", ".join([f"{k}({v})" for k, v in list(keywords.items())[:10]])}

请提供以下分析:
1. **市场概况**: 当前市场整体表现
2. **政策影响**: 分析宏观政策对市场的潜在影响
3. **情绪分析**: 市场情绪判断（贪婪/恐惧/中性）
4. **风险预警**: 可能的风险因素
5. **短期预测**: 未来1-3天的市场走势预测
6. **操作建议**: 基于分析的投资建议

请用中文回答，保持专业和客观。
"""

    async def _generate_report(self, prompt: str) -> str:
        try:
            response = await self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的金融市场分析师，擅长分析市场数据、宏观政策影响，并预测市场波动。请用中文回答，保持专业、客观、简洁。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=self.llm_temperature,
                max_tokens=2000,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[LLM Analysis Error]\nFailed to generate report: {e}\n\nPrompt:\n{prompt}"

    def _generate_summary(self, stocks: List, crypto: List, keywords: Dict) -> str:
        lines = ["📊 Market Snapshot"]

        if stocks:
            up = sum(1 for s in stocks if s.content.get("change_pct", 0) > 0)
            down = sum(1 for s in stocks if s.content.get("change_pct", 0) < 0)
            lines.append(f"📈 Stocks: {up} up, {down} down")

        if crypto:
            up = sum(1 for c in crypto if c.content.get("change_pct", 0) > 0)
            down = sum(1 for c in crypto if c.content.get("change_pct", 0) < 0)
            lines.append(f"₿ Crypto: {up} up, {down} down")

        if keywords:
            top_keywords = list(keywords.keys())[:5]
            lines.append(f"📰 Hot topics: {', '.join(top_keywords)}")

        return "\n".join(lines)

    async def check_anomalies(self) -> List[Dict]:
        data = await self.collect_all_data()
        anomalies: List[Dict] = []

        threshold = self.config.alerts.price_change_percent

        for dp in data.get("stocks", []):
            change = abs(dp.content.get("change_pct", 0))
            if change >= threshold:
                anomalies.append(
                    {
                        "type": "stock_price_alert",
                        "symbol": dp.content.get("symbol"),
                        "change_pct": dp.content.get("change_pct"),
                        "message": f"{dp.content.get('symbol')} 异动: {change:.2f}%",
                    }
                )

        for dp in data.get("crypto", []):
            change = abs(dp.content.get("change_pct", 0))
            if change >= threshold:
                anomalies.append(
                    {
                        "type": "crypto_price_alert",
                        "symbol": dp.content.get("symbol"),
                        "change_pct": dp.content.get("change_pct"),
                        "message": f"{dp.content.get('symbol')} 异动: {change:.2f}%",
                    }
                )

        return anomalies
