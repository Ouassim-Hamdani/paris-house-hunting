import sqlite3


class DeliveryRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def is_due_for_notification(self, user_id: int, offer_id: str, cooldown_hours: int = 24) -> bool:
        """Returns True if no delivery has been sent to user_id for offer_id within the cooldown window."""
        row = self.conn.execute(
            """
            SELECT 1 FROM deliveries
            WHERE user_id = ? AND offer_id = ?
            AND sent_at > datetime('now', ?)
            LIMIT 1
            """,
            (user_id, offer_id, f"-{cooldown_hours} hours"),
        ).fetchone()
        return row is None

    def record_delivery(self, user_id: int, offer_id: str) -> None:
        self.conn.execute(
            "INSERT INTO deliveries (user_id, offer_id, sent_at) VALUES (?, ?, datetime('now'))",
            (user_id, offer_id),
        )
        self.conn.commit()


