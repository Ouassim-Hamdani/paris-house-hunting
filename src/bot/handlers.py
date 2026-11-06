import html
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from src.config import Settings
from src.domain.models import Role, User, ProviderName
from src.storage.users import UserRepository
from src.storage.searches import SearchRepository
from src.storage.provider_status import ProviderStatusRepository
from src.providers.registry import build_registry, active
from src.bot.renderer import send_offer_notification


def get_db(context: ContextTypes.DEFAULT_TYPE):
    """Retrieve shared DB connection from bot application context."""
    return context.bot_data["db_conn"]


def require_registered(handler_func):
    """Decorator to enforce that a user is registered before accessing commands."""
    @wraps(handler_func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user:
            return
        conn = get_db(context)
        user_repo = UserRepository(conn)
        db_user = user_repo.get(user.id)

        if not db_user:
            await update.effective_message.reply_text(
                "⛔ <b>Access Denied!</b>\n\n"
                "Sorry, you have to register first ⛔!\n"
                "👉 Use: <code>/register &lt;password&gt;</code> 🔑",
                parse_mode="HTML",
            )
            return
        return await handler_func(update, context, *args, **kwargs)
    return wrapper


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Greets the user and checks registration status."""
    user = update.effective_user
    conn = get_db(context)
    user_repo = UserRepository(conn)
    db_user = user_repo.get(user.id)

    if not db_user:
        await update.message.reply_text(
            f"👋 <b>Welcome, {html.escape(user.first_name)}!</b> 🏠✨\n\n"
            "This is the <b>Paris House Hunting Notification System</b> 🤖\n"
            "We automatically track housing vacancies across <b>CROUS</b> & <b>ARPEJ</b>.\n\n"
            "⛔ <b>Sorry, you have to register first!</b> 🔒\n"
            "Please register with the password to start using the bot:\n"
            "👉 <code>/register &lt;password&gt;</code> 🔑",
            parse_mode="HTML",
        )
        return

    await update.message.reply_text(
        f"👋 <b>Welcome back, {html.escape(user.first_name)}!</b> 🏠✨\n\n"
        "Your bot is online and monitoring student housing vacancies! 🚀\n\n"
        "📋 <b>Available Commands:</b>\n"
        "• 🎓 <b>/crous</b> — Setup CROUS search (by city or link) 📍\n"
        "• 🏢 <b>/arpej</b> — Select monitored ARPEJ cities 🏙️\n"
        "• ⚡ <b>/now</b> — Check available housing right now! 🏡\n"
        "• 📊 <b>/status</b> — View your active alert settings 📋\n"
        "• 🔔 <b>/toggle_notify</b> — Enable or pause alerts 🔕\n"
        "• 💡 <b>/help</b> — Full command guide & pro-tips 📖",
        parse_mode="HTML",
    )


async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Registers a user with /register <password>."""
    user = update.effective_user
    conn = get_db(context)
    user_repo = UserRepository(conn)
    settings: Settings = context.bot_data["settings"]

    args = context.args
    if not args:
        await update.message.reply_text(
            "⚠️ <b>Usage:</b> <code>/register &lt;password&gt;</code> 🔑\n"
            "Provide the secret access password to register!",
            parse_mode="HTML",
        )
        return

    provided_password = args[0].strip()
    if provided_password != settings.register_password:
        await update.message.reply_text("❌ <b>Incorrect password!</b> Access denied ⛔", parse_mode="HTML")
        return

    existing = user_repo.get(user.id)
    if existing:
        await update.message.reply_text(
            "🤝 <b>You are already registered!</b> ✨\n\n"
            "Your account is active. Use <b>/status</b> to view your configuration or <b>/help</b> for commands. 💡",
            parse_mode="HTML",
        )
        return

    new_user = User(
        telegram_id=user.id,
        username=user.username or "",
        role=Role.MEMBER,
        notify_enabled=True,
    )
    user_repo.upsert(new_user)

    await update.message.reply_text(
        f"🎉 <b>Welcome to users list, {html.escape(user.first_name)}!</b> 🤝✨\n\n"
        "You'll be notified of future housing availabilities! 📢🔔\n\n"
        "🚀 <b>Get started by setting up your search targets:</b>\n"
        "• 🎓 <b>/crous</b> — Configure CROUS target (city, campus, or link) 📍\n"
        "• 🏢 <b>/arpej</b> — Select ARPEJ target cities 🏙️\n"
        "• ⚡ <b>/now</b> — Check vacancies immediately 🏡\n"
        "• 💡 <b>/help</b> — View full command directory 📖",
        parse_mode="HTML",
    )


@require_registered
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays user's active searches and notification status."""
    user = update.effective_user
    conn = get_db(context)
    user_repo = UserRepository(conn)
    search_repo = SearchRepository(conn)

    db_user = user_repo.get(user.id)
    s_crous = search_repo.get(user.id, ProviderName.CROUS)
    s_arpej = search_repo.get(user.id, ProviderName.ARPEJ)

    notif_status = "🟢 Enabled (Active alerts)" if db_user.notify_enabled else "🔴 Paused (Muted)"

    lines = [
        "📊 <b>Your Alert Configuration</b> ⚙️✨",
        "────────────────────────",
        f"🔔 <b>Notifications:</b> {notif_status}",
        "",
    ]

    # CROUS
    if s_crous and s_crous.active:
        label = s_crous.criteria.data.get("label", "Custom Area")
        lines.append(f"🎓 <b>CROUS Target:</b> 📍 <i>{html.escape(label)}</i> 🟢")
    else:
        lines.append("🎓 <b>CROUS Target:</b> ⚪ <i>Not configured (/crous)</i>")

    # ARPEJ
    if s_arpej and s_arpej.active:
        cities = s_arpej.criteria.data.get("cities", [])
        cities_str = ", ".join(c.title() for c in cities) if cities else "None"
        lines.append(f"🏙️ <b>ARPEJ Cities:</b> 🏢 <i>{html.escape(cities_str)}</i> 🟢")
    else:
        lines.append("🏙️ <b>ARPEJ Cities:</b> ⚪ <i>Not configured (/arpej)</i>")

    lines.append("────────────────────────")
    lines.append("💡 <i>Tip: Use <b>/crous</b> or <b>/arpej</b> to update your locations anytime!</i> 🔄")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


@require_registered
async def toggle_notify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggles background notifications on or off."""
    user = update.effective_user
    conn = get_db(context)
    user_repo = UserRepository(conn)
    db_user = user_repo.get(user.id)

    new_state = not db_user.notify_enabled
    user_repo.set_notify(user.id, new_state)

    if new_state:
        status_msg = (
            "🔔 <b>Notifications Activated!</b> 🟢✨\n\n"
            "Live background alerts are now ON. You will receive immediate pings when housing opens up! 📢🏡"
        )
    else:
        status_msg = (
            "🔕 <b>Notifications Paused!</b> 🔴\n\n"
            "Live background alerts are now MUTED. You won't receive background pings (you can still use <b>/now</b> anytime). 💤"
        )

    await update.message.reply_text(status_msg, parse_mode="HTML")


@require_registered
async def now_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Executes a search immediately for the requesting user."""
    user = update.effective_user
    conn = get_db(context)
    search_repo = SearchRepository(conn)

    s_crous = search_repo.get(user.id, ProviderName.CROUS)
    s_arpej = search_repo.get(user.id, ProviderName.ARPEJ)

    if (not s_crous or not s_crous.active) and (not s_arpej or not s_arpej.active):
        await update.message.reply_text(
            "⚠️ <b>No search configured!</b> 🎯\n\n"
            "Please configure at least one provider first:\n"
            "👉 🎓 <b>/crous</b> to set your CROUS area\n"
            "👉 🏙️ <b>/arpej</b> to pick ARPEJ cities",
            parse_mode="HTML",
        )
        return

    status_msg = await update.message.reply_text("🔎 <b>Scanning CROUS & ARPEJ for available housing...</b> ⏳⚡", parse_mode="HTML")

    registry = active(build_registry())
    found_offers = []

    # Run CROUS if configured
    if s_crous and s_crous.active and ProviderName.CROUS in registry:
        try:
            crous_offers = registry[ProviderName.CROUS].search(s_crous.criteria)
            found_offers.extend(crous_offers)
        except Exception as e:
            await update.message.reply_text(f"⚠️ <b>CROUS Error:</b> {html.escape(str(e))}")

    # Run ARPEJ if configured
    if s_arpej and s_arpej.active and ProviderName.ARPEJ in registry:
        try:
            arpej_offers = registry[ProviderName.ARPEJ].search(s_arpej.criteria)
            found_offers.extend(arpej_offers)
        except Exception as e:
            await update.message.reply_text(f"⚠️ <b>ARPEJ Error:</b> {html.escape(str(e))}")

    await status_msg.delete()

    if not found_offers:
        await update.message.reply_text(
            "🏡 <b>No housing available right now</b> matching your criteria ⚪\n\n"
            "Don't worry — we scan 24/7 every 5 minutes and will notify you the second something opens up! 🔔⚡",
            parse_mode="HTML",
        )
        return

    await update.message.reply_text(f"🎉 <b>Found {len(found_offers)} available listing(s)!</b> 🏡✨\nHere is what's currently open for booking: 👇", parse_mode="HTML")
    for offer in found_offers:
        await send_offer_notification(context.bot, user.id, offer)


@require_registered
async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only health dashboard."""
    user = update.effective_user
    conn = get_db(context)
    user_repo = UserRepository(conn)
    status_repo = ProviderStatusRepository(conn)
    settings: Settings = context.bot_data["settings"]

    db_user = user_repo.get(user.id)
    if not db_user or db_user.role != Role.ADMIN:
        await update.message.reply_text("⛔ <b>Sorry, you're not an admin!</b> 🚫", parse_mode="HTML")
        return

    statuses = status_repo.get_all()
    user_count = user_repo.count()
    interval_min = settings.scan_interval_seconds // 60

    lines = [
        "💓 <b>System Health & Diagnostics</b> 🤖⚙️",
        "────────────────────────",
        f"👥 <b>Registered Users:</b> {user_count} 👤",
        f"⏱️ <b>Scan Frequency:</b> Every {interval_min} min ({settings.scan_interval_seconds}s) 🔄",
        f"⚙️ <b>System Status:</b> 🟢 Online & Healthy",
        "",
        "📡 <b>Provider Scrapers:</b>",
    ]

    for s in statuses:
        status_icon = "🔴 Failed" if s.last_error else "🟢 Healthy"
        last_run = s.last_run_at.strftime("%H:%M:%S UTC") if s.last_run_at else "Never"
        provider_name = s.provider.value.upper()
        p_icon = "🎓" if s.provider == ProviderName.CROUS else "🏢"
        lines.append(f"• {p_icon} <b>{provider_name}:</b> {status_icon} (Last scan: <code>{last_run}</code>)")
        if s.last_error:
            lines.append(f"   ⚠️ <i>Error: {html.escape(s.last_error[:80])}</i>")

    lines.append("────────────────────────")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


@require_registered
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rich, beautiful command directory with emojis."""
    lines = [
        "🤖 <b>PARIS HOUSE HUNTING BOT — COMMAND DIRECTORY</b> 🏠✨",
        "<i>Automated 24/7 housing tracker for CROUS & ARPEJ residences.</i>",
        "",
        "⚡ <b>QUICK CONTROLS:</b>",
        "• 🚀 <b>/now</b> — Scan and show available housing right now! 🏡",
        "• 🔔 <b>/toggle_notify</b> — Switch live alert notifications 🟢 ON / 🔕 OFF",
        "• 📊 <b>/status</b> — View your active search targets & alert settings 📋",
        "",
        "🎯 <b>TARGET CONFIGURATION:</b>",
        "• 🎓 <b>/crous</b> — Configure CROUS target by city, university or direct link 📍",
        "• 🏙️ <b>/arpej</b> — Interactive multi-city selector for ARPEJ residences 🏢",
        "",
        "🔐 <b>ACCOUNT & SYSTEM:</b>",
        "• 🔑 <b>/register &lt;password&gt;</b> — Register and unlock bot access 🤝",
        "• 🩺 <b>/health</b> — System status & scraper diagnostics <i>(Admin only)</i> 🛠️",
        "• 💡 <b>/help</b> — Show this command directory 📖",
        "",
        "────────────────────────",
        "💡 <b>Pro-Tip:</b> <i>Configure both /crous and /arpej to maximize your chances of securing an apartment!</i> 🚀",
    ]

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")
