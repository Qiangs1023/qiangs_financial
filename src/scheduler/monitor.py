"""Market monitoring scheduler."""

import asyncio
import signal
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.analyzer.engine import MarketAnalyzer
from src.config import config
from src.notifier.dispatcher import NotificationDispatcher


scheduler = AsyncIOScheduler()
analyzer: MarketAnalyzer = None
notifier: NotificationDispatcher = None


def init():
    global analyzer, notifier
    analyzer = MarketAnalyzer(config)
    notifier = NotificationDispatcher(config.notifications)


async def job_market_snapshot():
    print(f"[{datetime.now()}] Running market snapshot...")
    result = await analyzer.analyze()
    print(result["summary"])


async def job_daily_report():
    print(f"[{datetime.now()}] Generating daily report...")
    result = await analyzer.analyze()

    report = f"""🌅 每日财经晨报
时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}

{result["summary"]}

详细分析:
{result["report"]}
"""
    notifier.send_all(report)


async def job_anomaly_alert():
    print(f"[{datetime.now()}] Checking for anomalies...")
    anomalies = await analyzer.check_anomalies()

    if anomalies:
        messages = ["⚠️ 市场异动预警:\n"]
        for a in anomalies:
            messages.append(f"• {a['message']}")
        notifier.send_all("\n".join(messages))


async def run_once():
    """Run analysis once and exit."""
    init()
    result = await analyzer.analyze()
    print(result["summary"])
    print("\n" + result["report"])


def start_scheduler():
    """Start the monitoring scheduler."""
    init()

    if config.scheduler.market_snapshot.enabled:
        scheduler.add_job(
            job_market_snapshot,
            CronTrigger.from_crontab(config.scheduler.market_snapshot.cron),
        )

    if config.scheduler.daily_report.enabled:
        scheduler.add_job(
            job_daily_report,
            CronTrigger.from_crontab(config.scheduler.daily_report.cron),
        )

    if config.scheduler.anomaly_alert.enabled:
        scheduler.add_job(
            job_anomaly_alert,
            CronTrigger.from_crontab(config.scheduler.anomaly_alert.cron),
        )

    def shutdown(signum, frame):
        print("\nShutting down...")
        scheduler.shutdown()
        asyncio.get_event_loop().stop()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    scheduler.start()
    print("Scheduler started. Jobs:")
    for job in scheduler.get_jobs():
        print(f"  - {job.id}: {job.trigger}")

    asyncio.get_event_loop().run_forever()
