import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def connect(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def current_version(conn: sqlite3.Connection) -> int:
    try:
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        return row[0] or 0
    except sqlite3.OperationalError:
        return 0


def migrate(conn: sqlite3.Connection) -> None:
    """Apply numbered *.sql files (001_..., 002_...) newer than the current version."""
    version = current_version(conn)
    for f in sorted(MIGRATIONS_DIR.glob("*.sql")):
        n = int(f.name.split("_", 1)[0])
        if n > version:
            conn.executescript(f.read_text(encoding="utf-8"))
            conn.execute("UPDATE schema_version SET version = ?", (n,))
            conn.commit()
