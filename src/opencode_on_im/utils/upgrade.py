from typing import Any

import httpx

from opencode_on_im import __version__
from opencode_on_im.core.config import Settings


async def check_upgrade(settings: Settings) -> dict[str, Any] | None:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                settings.upgrade_check_url,
                params={
                    "version": __version__,
                    "platform": "docker",
                },
            )

            if response.status_code == 200:
                data: dict[str, Any] = response.json()
                return data
    except Exception:
        pass

    return None
