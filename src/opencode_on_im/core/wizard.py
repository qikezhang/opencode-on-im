from rich.console import Console
from rich.prompt import Prompt, Confirm
import yaml

from opencode_on_im.core.config import Settings


console = Console()


def run_setup_wizard(config_path: str | None = None) -> None:
    console.print("\n[bold cyan]OpenCode-on-IM Setup Wizard[/bold cyan]\n")
    
    config: dict = {}
    
    console.print("[bold]Telegram Configuration[/bold]")
    if Confirm.ask("Enable Telegram bot?", default=True):
        token = Prompt.ask("Enter Telegram Bot Token")
        config["telegram"] = {"token": token}
    
    console.print("\n[bold]DingTalk Configuration[/bold]")
    if Confirm.ask("Enable DingTalk bot?", default=False):
        app_key = Prompt.ask("Enter DingTalk App Key")
        app_secret = Prompt.ask("Enter DingTalk App Secret", password=True)
        agent_id = Prompt.ask("Enter DingTalk Agent ID")
        config["dingtalk"] = {
            "app_key": app_key,
            "app_secret": app_secret,
            "agent_id": agent_id,
        }
    
    console.print("\n[bold]Proxy Configuration[/bold]")
    if Confirm.ask("Configure residential proxy?", default=False):
        proxy_url = Prompt.ask("Enter proxy URL (http://user:pass@host:port)")
        config["proxy"] = {"enabled": True, "url": proxy_url}
    
    output_path = config_path or "config.yaml"
    with open(output_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    
    console.print(f"\n[green]Configuration saved to {output_path}[/green]")
    console.print("\nRun [bold]opencode-on-im run[/bold] to start the bot.")
