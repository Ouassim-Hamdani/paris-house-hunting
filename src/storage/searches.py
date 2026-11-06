import json
import sqlite3

from src.domain.models import ProviderName, Search, SearchCriteria


class SearchRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get(self, user_id: int, provider: ProviderName) -> Search | None:
        row = self.conn.execute(
            "SELECT id, user_id, provider, criteria, active FROM searches WHERE user_id = ? AND provider = ?",
            (user_id, provider.value),
        ).fetchone()
        if not row:
            return None
        return Search(
            id=row["id"],
            user_id=row["user_id"],
            provider=ProviderName(row["provider"]),
            criteria=SearchCriteria(json.loads(row["criteria"])),
            active=bool(row["active"]),
        )

    def save(self, search: Search) -> int:
        """Upsert: one search per (user, provider)."""
        criteria_json = json.dumps(search.criteria.data, ensure_ascii=False)
        cur = self.conn.execute(
            """
            INSERT INTO searches (user_id, provider, criteria, active, updated_at)
            VALUES (?, ?, ?, ?, datetime('now'))
            ON CONFLICT(user_id, provider) DO UPDATE SET
                criteria = excluded.criteria,
                active = excluded.active,
                updated_at = datetime('now')
            """,
            (search.user_id, search.provider.value, criteria_json, int(search.active)),
        )
        self.conn.commit()
        return cur.lastrowid or (search.id or 0)

    def list_active(self) -> list[tuple[Search, bool]]:
        """Returns all active searches joined with user notification preference.
        Returns list of (Search, user_notify_enabled).
        """
        rows = self.conn.execute(
            """
            SELECT s.id, s.user_id, s.provider, s.criteria, s.active, u.notify_enabled
            FROM searches s
            JOIN users u ON u.telegram_id = s.user_id
            WHERE s.active = 1
            """
        ).fetchall()
        result = []
        for r in rows:
            search = Search(
                id=r["id"],
                user_id=r["user_id"],
                provider=ProviderName(r["provider"]),
                criteria=SearchCriteria(json.loads(r["criteria"])),
                active=bool(r["active"]),
            )
            result.append((search, bool(r["notify_enabled"])))
        return result

    def delete(self, user_id: int, provider: ProviderName) -> None:
        self.conn.execute(
            "DELETE FROM searches WHERE user_id = ? AND provider = ?",
            (user_id, provider.value),
        )
        self.conn.commit()
