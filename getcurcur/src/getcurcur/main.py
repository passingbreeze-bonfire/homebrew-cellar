import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing_extensions import Annotated
from typing import Optional
import json
import logging

from pathlib import Path
import shutil
from enum import Enum
from getcurcur.providers.korea import HanaBankProvider
from getcurcur.providers.base import ExchangeRateProvider
from getcurcur.exceptions import ProviderError, NetworkError
from getcurcur.browser_manager import get_browser_manager


# Setup logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Typer 애플리케이션 생성
app = typer.Typer(help="Get current currency exchange rates from various banks.")
console = Console()


class OutputFormat(str, Enum):
    """Output format options."""
    table = "table"
    json = "json"
    csv = "csv"


# Provider registry - will be expanded as more providers are added
PROVIDERS = {
    "korea": {
        "hana": HanaBankProvider,
        # Future: "kb": KBBankProvider,
        # Future: "shinhan": ShinhanBankProvider,
    },
    # Future: "usa": {...},
    # Future: "japan": {...},
}


def get_all_providers() -> dict:
    """Get all available providers organized by country."""
    result = {}
    for country, banks in PROVIDERS.items():
        for bank_name, provider_class in banks.items():
            key = f"{country}.{bank_name}"
            result[key] = provider_class
    return result


def get_provider(identifier: str) -> ExchangeRateProvider:
    """
    Get a provider instance by identifier.
    
    Args:
        identifier: Provider identifier (e.g., "hana" or "korea.hana")
    
    Returns:
        Provider instance
    
    Raises:
        ValueError: If provider not found
    """
    all_providers = get_all_providers()
    
    # Try direct match first
    if identifier in all_providers:
        return all_providers[identifier]()
    
    # Try adding default country prefix
    if "korea." + identifier in all_providers:
        return all_providers["korea." + identifier]()
    
    # Try matching just the bank name (backwards compatibility)
    for key, provider_class in all_providers.items():
        if key.split(".")[-1] == identifier:
            return provider_class()
    
    raise ValueError(f"Provider '{identifier}' not found")


@app.command()
def show(
    bank: Annotated[str, typer.Option("--bank", "-b", help="Bank provider (e.g., 'hana' or 'korea.hana')")] = "hana",
    currency: Annotated[Optional[str], typer.Option("--currency", "-c", help="Filter by currency code (e.g., USD, EUR)")] = None,
    format: Annotated[OutputFormat, typer.Option("--format", "-f", help="Output format")] = OutputFormat.table,
    no_cache: Annotated[bool, typer.Option("--no-cache", help="Disable cache and fetch fresh data")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose logging")] = False,
):
    """
    Display current exchange rates from specified bank.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        provider = get_provider(bank)
    except ValueError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        console.print("\nAvailable providers:")
        for key in get_all_providers().keys():
            console.print(f"  - {key}")
        raise typer.Exit(code=1)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(f"Fetching rates from {provider.get_provider_name()}...", total=None)
        
        rates = []
        browser_manager = get_browser_manager(headless=True)
        
        try:
            with browser_manager.browser_context() as context:
                rates = provider.get_rates(context, use_cache=not no_cache)
        except NetworkError as e:
            console.print(f"[bold red]Network error: {e}[/bold red]")
            raise typer.Exit(code=1)
        except ProviderError as e:
            console.print(f"[bold red]Provider error: {e}[/bold red]")
            raise typer.Exit(code=1)
        except Exception as e:
            console.print(f"[bold red]Unexpected error: {e}[/bold red]")
            logger.exception("Unexpected error occurred")
            raise typer.Exit(code=1)
    
    if not rates:
        console.print("[yellow]No exchange rate data found.[/yellow]")
        return
    
    # Filter by currency if specified
    if currency:
        currency = currency.upper()
        rates = [r for r in rates if r.get("code", "").upper() == currency]
        if not rates:
            console.print(f"[yellow]No data found for currency: {currency}[/yellow]")
            return
    
    # Output in requested format
    if format == OutputFormat.json:
        console.print(json.dumps(rates, ensure_ascii=False, indent=2))
    elif format == OutputFormat.csv:
        # CSV header
        console.print("Currency,Code,Cash Buy,Cash Sell,Provider,Country")
        for rate in rates:
            console.print(f"{rate['currency']},{rate['code']},{rate['cash_buy']},{rate['cash_sell']},"
                        f"{rate.get('provider', '')},{rate.get('country', '')}")
    else:  # table format
        table = Table(title=f"Exchange Rates from {provider.get_provider_name()}")
        table.add_column("Currency", justify="left", style="cyan", no_wrap=True)
        table.add_column("Code", style="magenta")
        table.add_column("Cash Buy", justify="right", style="green")
        table.add_column("Cash Sell", justify="right", style="yellow")
        
        for rate in rates:
            table.add_row(
                rate["currency"],
                rate["code"],
                rate["cash_buy"],
                rate["cash_sell"]
            )
        
        console.print(table)


@app.command()
def convert(
    amount: Annotated[float, typer.Argument(help="Amount to convert")],
    from_currency: Annotated[str, typer.Argument(help="Source currency code (e.g., USD)")],
    to_currency: Annotated[str, typer.Option("--to", "-t", help="Target currency code")] = "KRW",
    bank: Annotated[str, typer.Option("--bank", "-b", help="Bank provider")] = "hana",
    transaction: Annotated[str, typer.Option("--type", help="Transaction type: buy or sell")] = "buy",
):
    """
    Convert amount between currencies using current exchange rates.
    """
    try:
        provider = get_provider(bank)
    except ValueError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(code=1)
    
    transaction_type = "cash_buy" if transaction.lower() == "buy" else "cash_sell"
    
    browser_manager = get_browser_manager(headless=True)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Calculating...", total=None)
        
        try:
            with browser_manager.browser_context() as context:
                result = provider.convert_amount(
                    amount=amount,
                    from_currency=from_currency.upper(),
                    context=context,
                    to_currency=to_currency.upper(),
                    transaction_type=transaction_type
                )
        except NetworkError as e:
            console.print(f"[bold red]Network error: {e}[/bold red]")
            raise typer.Exit(code=1)
        except ProviderError as e:
            console.print(f"[bold red]Provider error: {e}[/bold red]")
            raise typer.Exit(code=1)
        except ValueError as e:
            console.print(f"[bold red]Invalid input: {e}[/bold red]")
            raise typer.Exit(code=1)
        except Exception as e:
            console.print(f"[bold red]Unexpected error: {e}[/bold red]")
            logger.exception("Unexpected error occurred during conversion")
            raise typer.Exit(code=1)
    
    if result is None:
        console.print(f"[yellow]Cannot convert {from_currency} to {to_currency}[/yellow]")
        raise typer.Exit(code=1)
    
    console.print(f"[bold green]{amount:,.2f} {from_currency.upper()} = {result:,.2f} {to_currency.upper()}[/bold green]")
    console.print(f"[dim]Rate type: Cash {transaction.capitalize()}[/dim]")
    console.print(f"[dim]Provider: {provider.get_provider_name()}[/dim]")


@app.command()
def list_providers():
    """
    List all available exchange rate providers.
    """
    table = Table(title="Available Providers")
    table.add_column("Identifier", style="cyan")
    table.add_column("Country", style="magenta")
    table.add_column("Bank", style="green")
    
    for key in sorted(get_all_providers().keys()):
        country, bank = key.split(".")
        table.add_row(key, country.upper(), bank.capitalize())
    
    console.print(table)


@app.command()
def clear_cache():
    """
    Clear all cached exchange rate data.
    """
    
    cache_dir = Path.home() / ".getcurcur" / "cache"
    
    if cache_dir.exists():
        try:
            shutil.rmtree(cache_dir)
            console.print("[bold green]Cache cleared successfully![/bold green]")
        except Exception as e:
            console.print(f"[bold red]Failed to clear cache: {e}[/bold red]")
            raise typer.Exit(code=1)
    else:
        console.print("[yellow]No cache to clear.[/yellow]")


@app.command()
def install_browsers():
    """
    Install Playwright browsers required for web scraping.
    """
    console.print("[bold green]Installing Playwright browsers...[/bold green]")
    import subprocess
    import sys
    
    try:
        # Run playwright install command
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            console.print("[bold green]✓ Chromium browser installed successfully![/bold green]")
        else:
            console.print(f"[bold red]Failed to install browser:[/bold red]")
            console.print(result.stderr)
            raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(code=1)


def version_callback(value: bool):
    """Show version information."""
    if value:
        from getcurcur.__about__ import __version__
        console.print(f"getcurcur version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[Optional[bool], typer.Option(
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version information"
    )] = None,
):
    """
    GetCurCur - Get current currency exchange rates from various banks.
    
    Examples:
        getcurcur show                     # Show rates from default bank (Hana)
        getcurcur show -b hana -c USD      # Show only USD rate from Hana Bank
        getcurcur show -f json              # Output as JSON
        getcurcur convert 100 USD           # Convert 100 USD to KRW
        getcurcur list-providers            # List all available providers
    """
    pass


if __name__ == "__main__":
    app()
