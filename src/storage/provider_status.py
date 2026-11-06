import sqlite3
from datetime import datetime, timezone

from src.domain.models import ProviderName, ProviderStatus


class ProviderStatusRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def record_run(self, provider: ProviderName, ok: bool = True, error: str | None = None) -> None:
        now_str = datetime.now(timezone.utc).isoformat()
        if ok:
            self.conn.execute(
                """
                INSERT INTO provider_status (provider, last_run_at, last_ok_at, last_error)
                VALUES (?, ?, ?, NULL)
                ON CONFLICT(provider) DO UPDATE SET
                    last_run_at = excluded.last_run_at,
                    last_ok_at = excluded.last_ok_at,
                    last_error = NULL
                """,
                (provider.value, now_str, now_str),
            )
        else:
            self.conn.execute(
                """
                INSERT INTO provider_status (provider, last_run_at, last_error)
                VALUES (?, ?, ?)
                ON CONFLICT(provider) DO UPDATE SET
                    last_run_at = excluded.last_run_at,
                    last_error = excluded.last_error
                """,
                (provider.value, now_str, error or "Unknown error"),
            )
        self.conn.commit()

    def get_all(self) -> list[ProviderStatus]:
        rows = self.conn.execute("SELECT provider, last_run_at, last_ok_at, last_error FROM provider_status").fetchall()
        statuses = []
        for r in rows:
            last_run = datetime.fromisoformat(r["last_run_at"]) if r["last_run_at"] else None
            last_ok = datetime.fromisoformat(r["last_ok_at"]) if r["last_ok_at"] else None
            statuses.append(
                ProviderStatus(
                    provider=ProviderName(r["provider"]),
                    last_run_at=last_run,
                    last_ok_at=last_ok,
                    last_error=r["last_error"],
                )
            )
        return statuses
