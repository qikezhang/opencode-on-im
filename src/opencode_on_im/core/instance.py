"""Instance registry and QR code generation."""

import hashlib
import hmac
import json
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime

import qrcode
import structlog
from rich.console import Console

from opencode_on_im.core.config import Settings

logger = structlog.get_logger()
console = Console()


@dataclass
class Instance:
    """Represents an OpenCode instance."""

    id: str
    name: str
    opencode_session_id: str
    connect_secret: str
    created_at: str
    qr_version: int = 1


class InstanceRegistry:
    """Manages instance registration and QR codes."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.instances_file = settings.data_dir / "instances.json"
        self._instances: dict[str, Instance] = {}
        self._load()

    def _load(self) -> None:
        """Load instances from file."""
        if self.instances_file.exists():
            try:
                with open(self.instances_file) as f:
                    data = json.load(f)
                self._instances = {k: Instance(**v) for k, v in data.items()}
            except Exception as e:
                logger.error("load_instances_failed", error=str(e))

    def _save(self) -> None:
        """Save instances to file."""
        self.settings.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.instances_file, "w") as f:
            json.dump(
                {k: asdict(v) for k, v in self._instances.items()},
                f,
                indent=2,
            )

    def create_instance(
        self, name: str | None = None, opencode_session_id: str | None = None
    ) -> Instance:
        """Create a new instance."""
        instance_id = secrets.token_urlsafe(16)

        if not name:
            base_name = "instance"
            counter = 1
            name = base_name
            while any(i.name == name for i in self._instances.values()):
                name = f"{base_name}-{counter}"
                counter += 1

        connect_secret = self._generate_secret(instance_id)

        instance = Instance(
            id=instance_id,
            name=name,
            opencode_session_id=opencode_session_id or "",
            connect_secret=connect_secret,
            created_at=datetime.utcnow().isoformat(),
        )

        self._instances[instance_id] = instance
        self._save()

        logger.info("instance_created", id=instance_id, name=name)
        return instance

    def get_instance(self, instance_id: str) -> Instance | None:
        """Get instance by ID."""
        return self._instances.get(instance_id)

    def get_instance_by_name(self, name: str) -> Instance | None:
        """Get instance by name."""
        for instance in self._instances.values():
            if instance.name == name:
                return instance
        return None

    def list_instances(self) -> list[Instance]:
        """List all instances."""
        return list(self._instances.values())

    def rename_instance(self, instance_id: str, new_name: str) -> bool:
        """Rename an instance."""
        if instance_id not in self._instances:
            return False

        if any(i.name == new_name for i in self._instances.values()):
            return False

        self._instances[instance_id].name = new_name
        self._save()
        return True

    def reset_qr(self, instance_id: str) -> Instance | None:
        """Reset QR code for an instance (invalidates old bindings)."""
        instance = self._instances.get(instance_id)
        if not instance:
            return None

        instance.qr_version += 1
        instance.connect_secret = self._generate_secret(instance_id, instance.qr_version)
        self._save()

        logger.info("qr_reset", instance_id=instance_id, version=instance.qr_version)
        return instance

    def delete_instance(self, instance_id: str) -> bool:
        """Delete an instance."""
        if instance_id in self._instances:
            del self._instances[instance_id]
            self._save()
            return True
        return False

    def verify_connect_secret(self, instance_id: str, secret: str) -> bool:
        """Verify a connect secret."""
        instance = self._instances.get(instance_id)
        if not instance:
            return False
        return hmac.compare_digest(instance.connect_secret, secret)

    def _generate_secret(self, instance_id: str, version: int = 1) -> str:
        """Generate HMAC secret for instance."""
        # Include version to ensure reset generates a different secret
        data = f"{instance_id}:{version}".encode()
        return hmac.new(
            self.settings.secret_key.encode(),
            data,
            hashlib.sha256,
        ).hexdigest()[:32]

    def generate_qr_data(self, instance: Instance) -> str:
        """Generate QR code data payload."""
        import base64

        payload = {
            "instance_id": instance.id,
            "instance_name": instance.name,
            "connect_secret": instance.connect_secret,
            "local_endpoint": f"{self.settings.opencode_host}:{self.settings.opencode_port}",
            "created_at": int(datetime.utcnow().timestamp()),
            "version": instance.qr_version,
        }

        return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()

    def generate_qr_image(self, instance: Instance) -> bytes:
        """Generate QR code image as PNG bytes."""
        from io import BytesIO

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.generate_qr_data(instance))
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()


def generate_qr_code(instance_name: str | None = None) -> None:
    """CLI command: Generate and display QR code."""
    settings = Settings()
    registry = InstanceRegistry(settings)

    if instance_name:
        instance = registry.get_instance_by_name(instance_name)
        if not instance:
            console.print(f"[red]Instance '{instance_name}' not found[/red]")
            return
    else:
        instances = registry.list_instances()
        if not instances:
            instance = registry.create_instance()
            console.print(f"[green]Created new instance: {instance.name}[/green]")
        else:
            instance = instances[0]

    qr_data = registry.generate_qr_data(instance)

    qr = qrcode.QRCode(box_size=1, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr.print_ascii(invert=True)

    console.print(f"\n[bold]Instance:[/bold] {instance.name}")
    console.print(f"[bold]ID:[/bold] {instance.id}")
    console.print("\n[yellow]Scan this QR code with Telegram or DingTalk to bind.[/yellow]")


def show_status() -> None:
    """CLI command: Show status of all instances."""
    settings = Settings()
    registry = InstanceRegistry(settings)

    instances = registry.list_instances()

    if not instances:
        console.print("[yellow]No instances registered.[/yellow]")
        return

    console.print("\n[bold]Registered Instances:[/bold]\n")

    for instance in instances:
        console.print(f"  [cyan]{instance.name}[/cyan]")
        console.print(f"    ID: {instance.id}")
        console.print(f"    Created: {instance.created_at}")
        console.print(f"    QR Version: {instance.qr_version}")
        console.print()
