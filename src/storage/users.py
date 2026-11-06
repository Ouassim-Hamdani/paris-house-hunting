from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from src.domain.models import Role, User


class UserRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get(self, telegram_id: int) -> User | None:
        row = self.conn.execute(
            "SELECT telegram_id, username, role, notify_enabled FROM users WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()
        if not row:
            return None
        return User(
            telegram_id=row["telegram_id"],
            username=row["username"],
            role=Role(row["role"]),
            notify_enabled=bool(row["notify_enabled"]),
        )

    def upsert(self, user: User) -> None:
        self.conn.execute(
            """
            INSERT INTO users (telegram_id, username, role, notify_enabled)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username = excluded.username,
                role = excluded.role,
                notify_enabled = excluded.notify_enabled
            """,
            (user.telegram_id, user.username, user.role.value, int(user.notify_enabled)),
        )
        self.conn.commit()

    def set_notify(self, telegram_id: int, enabled: bool) -> None:
        self.conn.execute(
            "UPDATE users SET notify_enabled = ? WHERE telegram_id = ?",
            (int(enabled), telegram_id),
        )
        self.conn.commit()

    def count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) FROM users").fetchone()
        return row[0] if row else 0
