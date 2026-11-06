import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    bot_token: str
    register_password: str
    db_path: str = "data/housing.sqlite3"
    scan_interval_seconds: int = 300

    @classmethod
    def from_env(cls) -> "Settings":
        from dotenv import load_dotenv

        load_dotenv()
        missing = [k for k in ("BOT", "PASSWORD") if not os.getenv(k)]
        if missing:
            raise RuntimeError(f"Missing env vars: {', '.join(missing)}")
        return cls(
            bot_token=os.environ["BOT"],
            register_password=os.environ["PASSWORD"],
            db_path=os.getenv("SQLITE_PATH", "data/housing.sqlite3"),
            scan_interval_seconds=int(os.getenv("SCAN_INTERVAL", "300")),
        )
