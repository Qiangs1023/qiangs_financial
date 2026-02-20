"""CLI entry point for FinPulse."""

import asyncio
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from src.config import config, settings
from src.scheduler.monitor import start_scheduler

app = typer.Typer(name="finpulse", help="Financial market monitoring and prediction system")
console = Console()


@app.command()
def analyze(
    market: str = typer.Option(
        "all", "--market", "-m", help="Market to analyze: a股, 美股, crypto, all"
    ),
    output: Path = typer.Option(None, "--output", "-o", help="Output file for report"),
):
    """Run a one-time market analysis."""
    from src.analyzer.engine import MarketAnalyzer

    console.print("[bold blue]Starting market analysis...[/]")

    analyzer = MarketAnalyzer(config)
    result = asyncio.run(analyzer.analyze(market))

    console.print(result["summary"])

    if output:
        output.write_text(result["report"], encoding="utf-8")
        console.print(f"[green]Report saved to {output}[/]")


@app.command()
def monitor(
    daemon: bool = typer.Option(False, "--daemon", "-d", help="Run as daemon"),
    once: bool = typer.Option(False, "--once", help="Run once and exit"),
):
    """Start continuous market monitoring."""
    if once:
        from src.scheduler.monitor import run_once

        asyncio.run(run_once())
    else:
        console.print("[bold green]Starting market monitor...[/]")
        console.print("Press Ctrl+C to stop")
        start_scheduler()


@app.command()
def test_notify():
    """Test notification channels."""
    from src.notifier.dispatcher import NotificationDispatcher

    dispatcher = NotificationDispatcher(config.notifications)

    message = f"FinPulse Test Notification\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    results = dispatcher.send_all(message)

    table = Table(title="Notification Test Results")
    table.add_column("Channel")
    table.add_column("Status")
    table.add_column("Details")

    for channel, status in results.items():
        table.add_row(
            channel,
            "[green]OK[/]" if status["success"] else "[red]FAILED[/]",
            status.get("message", ""),
        )

    console.print(table)


@app.command()
def config_check():
    """Validate and display current configuration."""
    console.print("[bold]Current Configuration:[/]")
    console.print(f"Config file: {settings.config_path}")
    console.print(
        f"\nMarkets: {len(config.markets.stocks)} stocks, {len(config.markets.crypto)} crypto"
    )
    console.print(f"News sources: {len(config.news.rss)} RSS feeds")
    console.print(f"Telegram enabled: {config.notifications.telegram.enabled}")
    console.print(f"WeChat enabled: {config.notifications.wechat.enabled}")


@app.command()
def init():
    """Initialize FinPulse configuration."""
    config_file = Path("config.yaml")
    env_file = Path(".env")

    if config_file.exists():
        console.print("[yellow]config.yaml already exists[/]")
    else:
        import shutil

        shutil.copy("config.example.yaml", "config.yaml")
        console.print("[green]Created config.yaml[/]")

    if env_file.exists():
        console.print("[yellow].env already exists[/]")
    else:
        import shutil

        shutil.copy(".env.example", ".env")
        console.print("[green]Created .env[/]")

    console.print("\n[bold]Next steps:[/]")
    console.print("1. Edit config.yaml to set your markets")
    console.print("2. Edit .env to add your API keys")
    console.print("3. Run [bold]finpulse analyze[/] to test")


if __name__ == "__main__":
    app()
