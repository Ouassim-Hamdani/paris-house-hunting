import asyncio
import logging
from pathlib import Path

from telegram.ext import Application, CommandHandler, ContextTypes

from src.config import Settings
from src.storage.db import connect, migrate
from src.providers.registry import build_registry, active
from src.services.scanner import Scanner
from src.bot.renderer import send_offer_notification
from src.bot.handlers import (
    start_command,
    register_command,
    status_command,
    toggle_notify_command,
    now_command,
    health_command,
    help_command,
)
from src.bot.conversations.crous import crous_conv_handler
from src.bot.conversations.arpej import arpej_conv_handler

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("housing_bot")


async def scheduled_scan_job(context: ContextTypes.DEFAULT_TYPE):
    """Periodic job that scans active searches and dispatches notifications."""
    db_conn = context.bot_data["db_conn"]
    providers = context.bot_data["providers"]
    scanner = Scanner(db_conn, providers)

    try:
        pending_notifs = await asyncio.to_thread(scanner.scan)
        if not pending_notifs:
            return

        log.info("Dispatched %d notifications", len(pending_notifs))
        for notif in pending_notifs:
            sent = await send_offer_notification(context.bot, notif.user_id, notif.offer)
            if sent:
                await asyncio.to_thread(scanner.record_delivery, notif.user_id, notif.offer.id)
    except Exception as e:
        log.exception("Error during scheduled scan: %s", e)


def main():
    settings = Settings.from_env()

    # Ensure database is migrated
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    db_conn = connect(settings.db_path)
    migrate(db_conn)
    log.info("Database migrated and ready at %s", settings.db_path)

    providers = active(build_registry())
    log.info("Active providers: %s", [p.value for p in providers.keys()])

    # Build single telegram application
    app = Application.builder().token(settings.bot_token).build()

    # Store shared resources in bot_data
    app.bot_data["db_conn"] = db_conn
    app.bot_data["settings"] = settings
    app.bot_data["providers"] = providers

    # Register conversations first (highest priority)
    app.add_handler(crous_conv_handler)
    app.add_handler(arpej_conv_handler)

    # Register standard commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("register", register_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("toggle_notify", toggle_notify_command))
    app.add_handler(CommandHandler("now", now_command))
    app.add_handler(CommandHandler("health", health_command))
    app.add_handler(CommandHandler("help", help_command))

    # Schedule periodic scanning job
    app.job_queue.run_repeating(
        scheduled_scan_job,
        interval=settings.scan_interval_seconds,
        first=5,  # first scan 5s after startup
        name="housing_scanner_job",
    )
    log.info(
        "Scheduled background scanner every %d seconds (%d minutes)",
        settings.scan_interval_seconds,
        settings.scan_interval_seconds // 60,
    )

    # Run polling
    log.info("Housing Bot v2 started! Polling Telegram...")
    app.run_polling()


if __name__ == "__main__":
    main()
