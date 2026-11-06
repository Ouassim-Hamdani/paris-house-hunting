# Admin Management Guide

To initialize or seed the admin user, run:

```bash
uv run python scripts/add_admin.py
```

This will ensure the database is migrated and upsert:
- **Telegram ID**: `814952835`
- **Username**: `Ouassim`
- **Role**: `Admin`

Using a custom database path:
```bash
uv run python scripts/add_admin.py 814952835 --db data/housing.sqlite3
```

### What This Does:
1. Automatically connects to the database (configured via `.env` or defaults to `data/housing.sqlite3`).
2. Runs database migrations if the database is new or needs updates.
3. Inserts or updates the user record with `role = 'Admin'`.
