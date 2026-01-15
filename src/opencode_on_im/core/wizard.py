import re
from collections.abc import Callable
from typing import Any

import yaml
from rich.console import Console
from rich.prompt import Confirm, Prompt

console = Console()


def validate_telegram_token(token: str) -> tuple[bool, str]:
    pattern = r"^\d{8,10}:[A-Za-z0-9_-]{35}$"
    if re.match(pattern, token):
        return True, ""
    return False, "Invalid format. Expected: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz1234567"


def validate_proxy_url(url: str) -> tuple[bool, str]:
    valid_schemes = ("http://", "https://", "socks5://", "socks4://")
    if not any(url.startswith(s) for s in valid_schemes):
        return False, f"URL must start with one of: {', '.join(valid_schemes)}"
    if "@" in url and ":" not in url.split("@")[0].split("://")[1]:
        return False, "Format: scheme://user:pass@host:port"
    return True, ""


def validate_not_empty(value: str, field_name: str) -> tuple[bool, str]:
    if not value.strip():
        return False, f"{field_name} cannot be empty"
    return True, ""


def prompt_with_validation(
    prompt_text: str,
    validator: Callable[[str], tuple[bool, str]],
    password: bool = False,
) -> str:
    while True:
        value = Prompt.ask(prompt_text, password=password)
        is_valid, error_msg = validator(value)
        if is_valid:
            return value
        console.print(f"[red]Error: {error_msg}[/red]")


def run_setup_wizard(config_path: str | None = None) -> None:
    console.print("\n[bold cyan]OpenCode-on-IM Setup Wizard[/bold cyan]\n")

    config: dict[str, Any] = {}
    has_platform = False

    console.print("[bold]Telegram Configuration[/bold]")
    if Confirm.ask("Enable Telegram bot?", default=True):
        token = prompt_with_validation(
            "Enter Telegram Bot Token",
            validate_telegram_token,
        )
        config["telegram"] = {"token": token}
        has_platform = True
        console.print("[green]✓ Telegram configured[/green]")

    console.print("\n[bold]DingTalk Configuration[/bold]")
    if Confirm.ask("Enable DingTalk bot?", default=False):
        app_key = prompt_with_validation(
            "Enter DingTalk App Key",
            lambda v: validate_not_empty(v, "App Key"),
        )
        app_secret = prompt_with_validation(
            "Enter DingTalk App Secret",
            lambda v: validate_not_empty(v, "App Secret"),
            password=True,
        )
        agent_id = Prompt.ask("Enter DingTalk Agent ID (optional)", default="")
        config["dingtalk"] = {
            "app_key": app_key,
            "app_secret": app_secret,
        }
        if agent_id:
            config["dingtalk"]["agent_id"] = agent_id
        has_platform = True
        console.print("[green]✓ DingTalk configured[/green]")

    if not has_platform:
        console.print("\n[yellow]Warning: No IM platform configured. At least one is required.[/yellow]")
        if not Confirm.ask("Continue anyway?", default=False):
            console.print("[red]Setup cancelled.[/red]")
            return

    console.print("\n[bold]Proxy Configuration[/bold]")
    console.print("[dim]Recommended for cloud servers to avoid IP blocks[/dim]")
    if Confirm.ask("Configure residential proxy?", default=False):
        proxy_url = prompt_with_validation(
            "Enter proxy URL (socks5://user:pass@host:port)",
            validate_proxy_url,
        )
        config["proxy"] = {"enabled": True, "url": proxy_url}
        console.print("[green]✓ Proxy configured[/green]")

    output_path = config_path or "config.yaml"
    with open(output_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    console.print(f"\n[green]✓ Configuration saved to {output_path}[/green]")
    console.print("\nNext steps:")
    console.print("  1. Run [bold]opencode-on-im run[/bold] to start the bot")
    console.print("  2. Open your IM app and find your bot")
    console.print("  3. Send /start to begin")
