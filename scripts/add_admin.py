"""Direct script to seed/ensure the initial admin user in the database."""
from pathlib import Path

from src.config import Settings
from src.domain.models import Role, User
from src.storage.db import connect, migrate
from src.storage.users import UserRepository

ADMIN_ID = 814952835
ADMIN_USERNAME = "Ouassim"


def main() -> None:
    settings = Settings.from_env()
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = connect(settings.db_path)
    migrate(conn)

    user_repo = UserRepository(conn)
    admin_user = User(
        telegram_id=ADMIN_ID,
        username=ADMIN_USERNAME,
        role=Role.ADMIN,
        notify_enabled=True,
    )
    user_repo.upsert(admin_user)
    print(f"Admin ready: ID={admin_user.telegram_id}, Username={admin_user.username!r}, Role={admin_user.role.value}")

if __name__ == "__main__":
    main()
