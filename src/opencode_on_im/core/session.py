"""Session management for multi-instance support."""

from datetime import datetime
from typing import Any

import aiosqlite
import structlog

from opencode_on_im.core.config import Settings

logger = structlog.get_logger()


class SessionManager:
    """Manages user sessions and instance bindings."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.db_path = settings.data_dir / "bindings.db"
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Initialize database connection and schema."""
        self.settings.data_dir.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self.db_path)
        await self._create_tables()

    async def close(self) -> None:
        """Close database connection."""
        if self._db:
            await self._db.close()

    async def _create_tables(self) -> None:
        """Create database tables if not exist."""
        assert self._db is not None

        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS bindings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                user_id TEXT NOT NULL,
                instance_id TEXT NOT NULL,
                bound_at TEXT NOT NULL,
                last_active TEXT NOT NULL,
                UNIQUE(platform, user_id, instance_id)
            )
        """)

        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS offline_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instance_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_bindings_user
            ON bindings(platform, user_id)
        """)

        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_offline_user
            ON offline_messages(platform, user_id)
        """)

        await self._db.commit()

    async def bind_user(self, platform: str, user_id: str, instance_id: str) -> bool:
        """Bind a user to an instance."""
        assert self._db is not None

        now = datetime.utcnow().isoformat()
        try:
            await self._db.execute(
                """
                INSERT INTO bindings (platform, user_id, instance_id, bound_at, last_active)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(platform, user_id, instance_id) DO UPDATE SET last_active = ?
                """,
                (platform, user_id, instance_id, now, now, now),
            )
            await self._db.commit()
            logger.info("user_bound", platform=platform, user_id=user_id, instance_id=instance_id)
            return True
        except Exception as e:
            logger.error("bind_failed", error=str(e))
            return False

    async def unbind_user(self, platform: str, user_id: str, instance_id: str) -> bool:
        """Unbind a user from an instance."""
        assert self._db is not None

        cursor = await self._db.execute(
            "DELETE FROM bindings WHERE platform = ? AND user_id = ? AND instance_id = ?",
            (platform, user_id, instance_id),
        )
        await self._db.commit()
        return cursor.rowcount > 0

    async def get_user_instances(self, platform: str, user_id: str) -> list[str]:
        """Get all instances bound to a user."""
        assert self._db is not None

        cursor = await self._db.execute(
            "SELECT instance_id FROM bindings WHERE platform = ? AND user_id = ?",
            (platform, user_id),
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

    async def get_instance_users(self, instance_id: str) -> list[tuple[str, str]]:
        """Get all users bound to an instance."""
        assert self._db is not None

        cursor = await self._db.execute(
            "SELECT platform, user_id FROM bindings WHERE instance_id = ?",
            (instance_id,),
        )
        rows = await cursor.fetchall()
        return [(str(row[0]), str(row[1])) for row in rows]

    async def update_last_active(self, platform: str, user_id: str) -> None:
        """Update last active timestamp for a user."""
        assert self._db is not None

        now = datetime.utcnow().isoformat()
        await self._db.execute(
            "UPDATE bindings SET last_active = ? WHERE platform = ? AND user_id = ?",
            (now, platform, user_id),
        )
        await self._db.commit()

    async def save_offline_message(
        self, instance_id: str, platform: str, user_id: str, content: str
    ) -> None:
        """Save a message for offline user."""
        assert self._db is not None

        now = datetime.utcnow().isoformat()

        count_cursor = await self._db.execute(
            """
            SELECT COUNT(*) FROM offline_messages
            WHERE platform = ? AND user_id = ?
            """,
            (platform, user_id),
        )
        row = await count_cursor.fetchone()
        count: int = row[0] if row else 0

        if count >= self.settings.max_offline_messages:
            await self._db.execute(
                """
                DELETE FROM offline_messages WHERE id IN (
                    SELECT id FROM offline_messages
                    WHERE platform = ? AND user_id = ?
                    ORDER BY created_at ASC
                    LIMIT ?
                )
                """,
                (platform, user_id, count - self.settings.max_offline_messages + 1),
            )

        await self._db.execute(
            """
            INSERT INTO offline_messages (instance_id, user_id, platform, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (instance_id, user_id, platform, content, now),
        )
        await self._db.commit()

    async def get_offline_messages(self, platform: str, user_id: str) -> list[dict[str, Any]]:
        """Get and clear offline messages for a user."""
        assert self._db is not None

        cursor = await self._db.execute(
            """
            SELECT instance_id, content, created_at FROM offline_messages
            WHERE platform = ? AND user_id = ?
            ORDER BY created_at ASC
            """,
            (platform, user_id),
        )
        messages = [
            {"instance_id": row[0], "content": row[1], "created_at": row[2]}
            for row in await cursor.fetchall()
        ]

        await self._db.execute(
            "DELETE FROM offline_messages WHERE platform = ? AND user_id = ?",
            (platform, user_id),
        )
        await self._db.commit()

        return messages
