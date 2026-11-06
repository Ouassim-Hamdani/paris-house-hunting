# Admin Management Guide

To initialize or seed the admin user, run:

```bash
uv run python scripts/add_admin.py
```

This will ensure the database is migrated and upsert:
- **Telegram ID**: `814952835`
- **Username**: `Ouassim`
- **Role**: `Admin`

Run from the project root (`PYTHONPATH="."` is needed outside Docker):
```bash
PYTHONPATH="." uv run scripts/add_admin.py
```

Or inside the Docker container:
```bash
docker compose exec bot python scripts/add_admin.py
```

### What This Does:
1. Automatically connects to the database at the fixed path `data/housing.sqlite3` (not configurable).
2. Runs database migrations if the database is new or needs updates.
3. Inserts or updates the user record with `role = 'Admin'`.

### Troubleshooting: `attempt to write a readonly database`

```
sqlite3.OperationalError: attempt to write a readonly database
```

The Docker container runs as root, so `data/` and `data/housing.sqlite3` are owned by `root` and your user cannot write to them. SQLite needs write access to both the file and its directory (for the WAL files). Fix:

```bash
sudo chown -R "$USER:$USER" data
```

or run the script inside the container (see above).
