import sqlite3
from datetime import datetime, timezone

from src.domain.models import Offer, ProviderName


class OfferRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def upsert_many(self, offers: list[Offer]) -> None:
        if not offers:
            return
        now_str = datetime.now(timezone.utc).isoformat()
        records = [
            (
                o.id,
                o.provider.value,
                o.name,
                o.url,
                o.address,
                o.postcode,
                o.city,
                o.price,
                o.size,
                o.image_url,
                1,
                now_str,
                now_str,
            )
            for o in offers
        ]
        self.conn.executemany(
            """
            INSERT INTO offers (id, provider, name, url, address, postcode, city, price, size, image_url, available, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                url = excluded.url,
                address = excluded.address,
                postcode = excluded.postcode,
                city = excluded.city,
                price = excluded.price,
                size = excluded.size,
                image_url = excluded.image_url,
                available = 1,
                last_seen = excluded.last_seen
            """,
            records,
        )
        self.conn.commit()

    def mark_unavailable_except(self, provider: ProviderName, active_ids: set[str]) -> None:
        """Mark offers from this provider as unavailable (available=0) if not in active_ids."""
        if not active_ids:
            self.conn.execute(
                "UPDATE offers SET available = 0 WHERE provider = ?",
                (provider.value,),
            )
        else:
            placeholders = ",".join("?" for _ in active_ids)
            self.conn.execute(
                f"UPDATE offers SET available = 0 WHERE provider = ? AND id NOT IN ({placeholders})",
                (provider.value, *active_ids),
            )
        self.conn.commit()
