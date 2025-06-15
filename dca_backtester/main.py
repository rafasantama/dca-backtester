"""Main entry point for the DCA Backtester."""

import logging
from datetime import datetime, timedelta, UTC
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from .backtester import DCABacktester
from .client.coingecko import CoinGeckoClient
from .exceptions import BacktestError
from .models import DCAPlan, Frequency
from .utils.ai_insights import get_ai_insights

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)

logger = logging.getLogger("dca_backtester")
console = Console()

app = typer.Typer(
    name="dca-backtester",
    help="A backtesting tool for Dollar Cost Averaging (DCA) cryptocurrency investment strategies",
    add_completion=False,
)

def validate_date_range(start_date: str, end_date: str) -> None:
    """Validate that the date range is within CoinGecko's free API window (last 365 days, not in the future)."""
    today = datetime.now(UTC).date()
    max_date = today
    min_date = today - timedelta(days=365)
    
    try:
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] Invalid date format. Please use YYYY-MM-DD format.")
        raise typer.Exit(1)

    if start < min_date:
        console.print(f"[bold red]Error:[/bold red] Start date {start} is too old. CoinGecko's free API only provides data from {min_date} to {max_date}.")
        raise typer.Exit(1)
    if end > max_date:
        console.print(f"[bold red]Error:[/bold red] End date {end} is in the future. Please use a date up to {max_date}.")
        raise typer.Exit(1)
    if start > end:
        console.print(f"[bold red]Error:[/bold red] Start date {start} is after end date {end}.")
        raise typer.Exit(1)

def load_settings() -> None:
    """Load settings from environment variables."""
    # No API key needed for CoinGecko
    pass

@app.command()
def run(
    symbol: str = typer.Argument(..., help="Cryptocurrency symbol (e.g., BTC, ETH)"),
    frequency: Frequency = typer.Option(
        Frequency.WEEKLY,
        "--frequency",
        "-f",
        help="Investment frequency",
    ),
    amount: float = typer.Option(
        100.0,
        "--amount",
        "-a",
        help="Investment amount per period",
    ),
    start_date: str = typer.Option(
        ...,
        "--start-date",
        "-s",
        help="Start date (YYYY-MM-DD)",
    ),
    end_date: str = typer.Option(
        ...,
        "--end-date",
        "-e",
        help="End date (YYYY-MM-DD)",
    ),
    sell_threshold: Optional[float] = typer.Option(
        None,
        "--sell-threshold",
        help="Sell threshold as a percentage (e.g., 50 for 50% profit)",
    ),
) -> None:
    """Run a DCA backtest simulation."""
    try:
        # Validate date range for CoinGecko API
        validate_date_range(start_date, end_date)

        # Load settings
        load_settings()

        # Create DCA plan
        plan = DCAPlan(
            symbol=symbol,
            frequency=frequency,
            amount=amount,
            start_date=start_date,
            end_date=end_date,
            sell_threshold=sell_threshold,
        )

        # Initialize client and backtester
        client = CoinGeckoClient()
        backtester = DCABacktester(client)

        # Run backtest
        results = backtester.run(plan)

        # Display results
        display_results(results)

        # Get AI insights
        insights = get_ai_insights(results)
        if insights:
            console.print("\n[bold blue]AI Insights:[/bold blue]")
            console.print(insights)

    except BacktestError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")
        raise typer.Exit(1)


def display_results(results: dict) -> None:
    """Display backtest results in a formatted table.

    Args:
        results: Dictionary containing backtest results
    """
    # Create tables for different sections
    params_table = Table(title="Simulation Parameters", show_header=True, header_style="bold magenta")
    params_table.add_column("Parameter", style="dim")
    params_table.add_column("Value")

    metrics_table = Table(title="Performance Metrics", show_header=True, header_style="bold green")
    metrics_table.add_column("Metric", style="dim")
    metrics_table.add_column("Value")

    trades_table = Table(title="Trade History", show_header=True, header_style="bold blue")
    trades_table.add_column("Date", style="dim")
    trades_table.add_column("Type")
    trades_table.add_column("Amount")
    trades_table.add_column("Price")
    trades_table.add_column("Value")

    # Add simulation parameters
    params_table.add_row("Symbol", results["symbol"])
    params_table.add_row("Frequency", results["frequency"])
    params_table.add_row("Amount per Period", f"${results['amount_per_period']:.2f}")
    params_table.add_row("Start Date", results["start_date"])
    params_table.add_row("End Date", results["end_date"])
    if results.get("sell_threshold"):
        params_table.add_row("Sell Threshold", f"{results['sell_threshold']}%")

    # Add performance metrics
    metrics_table.add_row("Total Invested", f"${results['total_invested']:.2f}")
    metrics_table.add_row("Final Value", f"${results['final_value']:.2f}")
    metrics_table.add_row("ROI", f"{results['roi']:.2f}%")
    metrics_table.add_row("APY", f"{results['apy']:.2f}%")
    metrics_table.add_row("Number of Trades", str(results["number_of_trades"]))
    metrics_table.add_row("Average Buy Price", f"${results['average_buy_price']:.2f}")
    metrics_table.add_row("Average Sell Price", f"${results['average_sell_price']:.2f}")
    metrics_table.add_row("Volatility", f"{results['volatility']:.2f}%")
    metrics_table.add_row("Sharpe Ratio", f"{results['sharpe_ratio']:.2f}")

    # Add trade history
    for trade in results["trades"]:
        trades_table.add_row(
            trade["date"],
            trade["type"],
            f"${trade['amount']:.2f}",
            f"${trade['price']:.2f}",
            f"${trade['value']:.2f}",
        )

    # Display tables
    console.print(params_table)
    console.print("\n")
    console.print(metrics_table)
    console.print("\n")
    console.print(trades_table)


if __name__ == "__main__":
    app() 