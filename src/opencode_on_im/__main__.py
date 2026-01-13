"""CLI entry point for opencode-on-im."""

import asyncio
import sys

import click
from rich.console import Console

from opencode_on_im.core.config import Settings, load_settings
from opencode_on_im.core.app import Application


console = Console()


@click.group()
@click.version_option()
def cli() -> None:
    """OpenCode-on-IM: Connect OpenCode to Telegram & DingTalk."""
    pass


@cli.command()
@click.option("--config", "-c", type=click.Path(), help="Path to config file")
def run(config: str | None) -> None:
    """Start the IM bot service."""
    try:
        settings = load_settings(config)
        app = Application(settings)
        asyncio.run(app.run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--config", "-c", type=click.Path(), help="Path to config file")
def setup(config: str | None) -> None:
    """Interactive setup wizard."""
    from opencode_on_im.core.wizard import run_setup_wizard
    
    run_setup_wizard(config)


@cli.command()
@click.argument("instance_name", required=False)
def qrcode(instance_name: str | None) -> None:
    """Generate QR code for instance binding."""
    from opencode_on_im.core.instance import generate_qr_code
    
    generate_qr_code(instance_name)


@cli.command()
def status() -> None:
    """Show current status of all instances and bindings."""
    from opencode_on_im.core.instance import show_status
    
    show_status()


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
