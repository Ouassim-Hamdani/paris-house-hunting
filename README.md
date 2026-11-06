# 🏠 Paris House Hunting (v2)

Automated student housing monitor for France (CROUS and ARPEJ), featuring real-time alerts dispatched through a Telegram bot.

---

## ✨ Features in v2

- **Single Async Process**: Built with `python-telegram-bot` (v22+), running bot polling and background scanning within a single unified process (no multi-process Unix signals or pipes).
- **Direct API Adapters**:
  - **CROUS**: Uses the official CROUS JSON Search API with Photon geocoding for precise bounding-box queries (supports direct URL pasting or searching by city/university name).
  - **ARPEJ**: Uses ARPEJ's WordPress REST API with dynamic city discovery across 60 cities and localized room-availability filtering.
- **SQLite Persistence**: ACID storage tracking registered users, per-user search profiles, canonical offer states, and notification logs.
- **24-Hour Anti-Spam Window**: Users are not spammed repeatedly for the same listing—re-notifications only trigger if an accommodation remains available after 24 hours.
- **Docker-ready**: Multi-stage image and `docker compose up -d` deployment with a persistent SQLite volume.
- **Interactive In-Chat Setup**:
  - `/crous`: Interactive geocoding or link configuration.
  - `/arpej`: Interactive paginated multi-select keyboard to toggle target cities.
  - `/now`: On-demand search bypassing cooldowns.
  - `/health`: Scraper diagnostics dashboard for administrators.

---

## 📁 Project Architecture

```
.
├── src/
│   ├── app.py                     # Main application entrypoint (Bot + Background Scanner)
│   ├── config.py                  # Environment settings validation
│   ├── domain/
│   │   └── models.py              # Normalized Offer, Search, User, Role
│   ├── providers/
│   │   ├── base.py                # Abstract Provider interface
│   │   ├── http.py                # Shared requests session with retries
│   │   ├── registry.py            # Provider registry
│   │   ├── crous/                 # CROUS client, bounds, geocoding & config
│   │   └── arpej/                 # ARPEJ client, city normalization & config
│   ├── storage/
│   │   ├── db.py                  # SQLite connection & migration runner
│   │   ├── migrations/            # Versioned SQL migrations (001_init.sql)
│   │   ├── users.py               # UserRepository
│   │   ├── searches.py            # SearchRepository
│   │   ├── offers.py              # OfferRepository
│   │   ├── deliveries.py          # DeliveryRepository (24h anti-spam log)
│   │   └── provider_status.py     # Health status tracking
│   ├── services/
│   │   └── scanner.py             # Scanner service with query batching & error isolation
│   └── bot/
│       ├── renderer.py            # HTML card formatting & photo sending
│       ├── handlers.py            # /start, /register, /status, /now, /health
│       └── conversations/
│           ├── crous.py           # /crous interactive setup
│           └── arpej.py           # /arpej interactive city multi-select
├── scripts/
│   └── add_admin.py               # Seed or promote an admin user
├── docs/
│   ├── database_schema.md         # Database documentation with Mermaid ER diagram
│   └── admin_management.md        # Admin setup instructions
├── Dockerfile                     # Multi-stage image (uv build → slim runtime)
├── docker-compose.yml             # One-command deployment with persistent ./data
├── .env.example                   # Configuration template
├── Makefile                       # Shortcuts for classic & Docker runs
├── pyproject.toml / uv.lock
└── README.md
```

---

## ⚙️ Configuration (`.env`)

All settings are read from a `.env` file in the project root. Start from the provided template:

```bash
cp .env.example .env            # Linux / macOS
Copy-Item .env.example .env     # Windows PowerShell
```

Then edit `.env`:

| Variable | Required | Default | Description |
| :--- | :---: | :--- | :--- |
| `BOT` | ✅ | — | Telegram bot token from [@BotFather](https://t.me/BotFather) |
| `PASSWORD` | ✅ | — | Password users send with `/register <password>` |
| `SQLITE_PATH` | | `data/housing.sqlite3` | SQLite database path (forced to `/app/data/housing.sqlite3` under Docker) |
| `SCAN_INTERVAL` | | `300` | Seconds between background scans |
| `CROUS_TOOL_ID` | | `47` | CROUS campaign ID (47 = 2026-2027) |

Example (`.env.example`):

```env
BOT=123456789:ABCDefghIJKlmNoPQRsTUVwxyZ
PASSWORD=change-me
SQLITE_PATH=data/housing.sqlite3
SCAN_INTERVAL=300
CROUS_TOOL_ID=47
```

> ⚠️ Never commit `.env`. It is ignored by both `.gitignore` and `.dockerignore`, so it is never baked into the image.

> ⚠️ Run only **one** instance per bot token. Telegram rejects two processes polling the same bot (`Conflict: terminated by other getUpdates request`), so stop the classic run before starting the container, and vice versa.

---

## 🐳 Option 1: Docker (recommended)

Requirements: [Docker](https://docs.docker.com/get-docker/) with Compose (Docker Desktop on Windows/macOS).

```bash
# 1. Configure
cp .env.example .env          # then fill in BOT and PASSWORD

# 2. Build & start in the background (auto-restarts on crash / reboot)
docker compose up -d --build

# 3. Follow logs
docker compose logs -f
```

| Action | Command | Makefile |
| :--- | :--- | :--- |
| Start / rebuild | `docker compose up -d --build` | `make docker-up` |
| Logs | `docker compose logs -f --tail=100` | `make docker-logs` |
| Status | `docker compose ps` | |
| Stop | `docker compose down` | `make docker-down` |
| Update | `git pull && docker compose up -d --build` | |

Notes:
- After editing `.env`, run `docker compose up -d` (recreates the container). `docker compose restart` does **not** reload `.env`.
- The database is stored in `./data/housing.sqlite3` on the host, so it survives rebuilds and is the same file the classic run uses.
- To seed an admin, run `scripts/add_admin.py` from the host as in Option 2 (it writes to the same `./data` database), then `docker compose restart`.

---

## 🐍 Option 2: Classic run (no Docker)

This project uses [`uv`](https://docs.astral.sh/uv/) for Python dependency management (Python 3.13+). Make sure `.env` is configured before starting.

### 1. Install Dependencies
```bash
uv sync
```

### 2. Seed Admin User
Set up your Telegram ID as an Admin for diagnostics and immediate access:
- **Linux / macOS**:
  ```bash
  PYTHONPATH="." uv run python scripts/add_admin.py
  ```
- **Windows (PowerShell)**:
  ```powershell
  $env:PYTHONPATH="."; uv run python scripts/add_admin.py
  ```

---

### 🐧 Running on Linux

#### Option A: Quick Background Run via `Makefile`
A dedicated `Makefile` is provided for running as a detached background daemon:

```bash
# 1. Start bot in the background (writes logs to logs/app.log)
make run

# 2. Check if the bot process is currently running
make check

# 3. View live output logs
tail -f logs/app.log

# 4. Stop the bot when needed
make stop
```

#### Option B: Foreground Run
```bash
PYTHONPATH="." uv run src/app.py
```

#### Option C: Production 24/7 Daemon (`systemd`)
For long-term servers (Ubuntu/Debian) that should restart automatically after a reboot:

1. **Create a systemd service file** (`/etc/systemd/system/housing-bot.service`):
   ```ini
   [Unit]
   Description=Housing Bot v2 Service
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/Logement
   Environment="PYTHONPATH=."
   ExecStart=/home/ubuntu/.cargo/bin/uv run src/app.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

2. **Enable and start the service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now housing-bot
   ```

3. **Check logs**:
   ```bash
   sudo journalctl -u housing-bot -f
   ```

---

### 🪟 Running on Windows

To ensure Python resolves imports within the `src/` directory, set `PYTHONPATH`:

#### PowerShell:
```powershell
$env:PYTHONPATH="."
uv run src/app.py
```
*(Or in a single line: `$env:PYTHONPATH="."; uv run src/app.py`)*

#### Command Prompt (cmd.exe):
```cmd
set PYTHONPATH=.
uv run src/app.py
```

#### Module Runner (No explicit PYTHONPATH needed):
```powershell
uv run python -m src.app
```

> If `uv sync` fails with `Access is denied` on `.venv\lib64`, the `.venv` was created from WSL/Linux. Delete `.venv` and run `uv sync` again from Windows.

---

## 💬 Bot Commands

| Command | Description | Access |
| :--- | :--- | :--- |
| `/start` | Welcome message and registration check | Public |
| `/register <password>` | Authenticate and register with the bot | Public |
| `/crous` | Configure CROUS search (search by city or paste link) 🎓 | Registered |
| `/arpej` | Interactive inline keyboard to select ARPEJ cities 🏙️ | Registered |
| `/status` | View your currently active search criteria 📊 | Registered |
| `/now` | Run an on-demand search and receive listings immediately ⚡ | Registered |
| `/toggle_notify` | Toggle background notifications on or off 🔔 | Registered |
| `/help` | Rich command directory & user guide 💡 | Registered |
| `/health` | View scraper status and registered user stats 🩺 | Admin |

---

## 📚 Documentation

- [Database Schema & ER Diagram](docs/database_schema.md)
- [Admin Management Guide](docs/admin_management.md)
