import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from src.domain.models import ProviderName, Search, SearchCriteria
from src.providers.crous import CrousProvider
from src.storage.searches import SearchRepository
from src.storage.users import UserRepository

WAITING_FOR_CROUS_INPUT = 1


def get_db(context: ContextTypes.DEFAULT_TYPE):
    return context.bot_data["db_conn"]


async def crous_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /crous command."""
    user = update.effective_user
    conn = get_db(context)
    user_repo = UserRepository(conn)

    if not user_repo.get(user.id):
        await update.message.reply_text(
            "⛔ <b>Access Denied!</b>\n\n"
            "Sorry, you have to register first ⛔!\n"
            "👉 Use: <code>/register &lt;password&gt;</code> 🔑",
            parse_mode="HTML",
        )
        return ConversationHandler.END

    # Check if user already provided argument: /crous Paris
    if context.args:
        query = " ".join(context.args)
        return await handle_crous_query(update, context, query)

    await update.message.reply_text(
        "📍 <b>CROUS Search Setup</b> 🎓✨\n"
        "────────────────────────\n"
        "Please send the <b>name of the city, campus or university</b> you want to track:\n"
        "<i>(e.g., Paris, Saclay, Lyon, Créteil, Orsay...)</i> 🏙️\n\n"
        "...OR paste a direct search link from 🌐 <code>trouverunlogement.lescrous.fr</code>!\n\n"
        "<i>Send /cancel to abort at any time.</i> ❌",
        parse_mode="HTML",
    )
    return WAITING_FOR_CROUS_INPUT


async def crous_text_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User typed a query or pasted a link."""
    user = update.effective_user
    conn = get_db(context)
    user_repo = UserRepository(conn)

    if not user_repo.get(user.id):
        await update.message.reply_text(
            "⛔ <b>Access Denied!</b>\n\n"
            "Sorry, you have to register first ⛔!\n"
            "👉 Use: <code>/register &lt;password&gt;</code> 🔑",
            parse_mode="HTML",
        )
        return ConversationHandler.END

    text = update.message.text.strip()
    return await handle_crous_query(update, context, text)


async def handle_crous_query(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str) -> int:
    provider = CrousProvider()
    conn = get_db(context)
    search_repo = SearchRepository(conn)
    user_id = update.effective_user.id

    # 1. Did the user paste a CROUS link?
    if "trouverunlogement.lescrous.fr" in query:
        try:
            criteria = provider.criteria_from_link(query)
            search_repo.save(Search(user_id=user_id, provider=ProviderName.CROUS, criteria=criteria))
            await update.effective_message.reply_text(
                "🎉 <b>CROUS Search Saved Successfully!</b> 🎓✅\n"
                "────────────────────────\n"
                "📍 <b>Target:</b> <i>Custom CROUS Link</i>\n"
                "🔔 <b>Alerts:</b> You will be notified the moment an accommodation opens up! ⚡",
                parse_mode="HTML",
            )
            return ConversationHandler.END
        except Exception as e:
            await update.effective_message.reply_text(
                f"❌ <b>Invalid link:</b> {html.escape(str(e))}\n"
                "Please verify the URL and try again, or type a city name 🏙️:",
                parse_mode="HTML",
            )
            return WAITING_FOR_CROUS_INPUT

    # 2. Otherwise treat as geocoding search
    status_msg = await update.effective_message.reply_text("🔎 <b>Searching geographic coordinates...</b> ⏳", parse_mode="HTML")
    try:
        results = provider.geocode(query, limit=5)
    except Exception as e:
        await status_msg.edit_text(f"❌ <b>Geocoding error:</b> {html.escape(str(e))}", parse_mode="HTML")
        return ConversationHandler.END

    await status_msg.delete()

    if not results:
        await update.effective_message.reply_text(
            f"❌ <b>No location found in France for</b> <i>{html.escape(query)}</i> 🇫🇷\n"
            "Please check the spelling and try again:",
            parse_mode="HTML",
        )
        return WAITING_FOR_CROUS_INPUT

    # Store candidate results in user_data
    context.user_data["crous_candidates"] = {str(i): r for i, r in enumerate(results)}

    # Build inline buttons for each candidate
    buttons = []
    for i, r in enumerate(results):
        buttons.append([InlineKeyboardButton(f"📍 {r.label}", callback_data=f"crous_pick:{i}")])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="crous_cancel")])

    await update.effective_message.reply_text(
        "📍 <b>Select the exact location to monitor:</b> 🎯",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML",
    )
    return WAITING_FOR_CROUS_INPUT


async def crous_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    conn = get_db(context)
    user_repo = UserRepository(conn)

    if not user_repo.get(user.id):
        await query.message.reply_text(
            "⛔ <b>Access Denied!</b>\n\n"
            "Sorry, you have to register first ⛔!\n"
            "👉 Use: <code>/register &lt;password&gt;</code> 🔑",
            parse_mode="HTML",
        )
        return ConversationHandler.END

    data = query.data
    if data == "crous_cancel":
        await query.edit_message_text("❌ <b>CROUS setup cancelled.</b>", parse_mode="HTML")
        return ConversationHandler.END

    if data.startswith("crous_pick:"):
        idx = data.split(":")[1]
        candidates = context.user_data.get("crous_candidates", {})
        chosen = candidates.get(idx)
        if not chosen:
            await query.edit_message_text("⚠️ <b>Session expired.</b> Please send <b>/crous</b> again. 🔄", parse_mode="HTML")
            return ConversationHandler.END

        search_repo = SearchRepository(conn)
        provider = CrousProvider()
        criteria = provider.criteria_from_geo(chosen)

        search_repo.save(Search(
            user_id=update.effective_user.id,
            provider=ProviderName.CROUS,
            criteria=criteria,
        ))

        await query.edit_message_text(
            f"🎉 <b>CROUS Target Updated!</b> 🎓✅\n"
            "────────────────────────\n"
            f"📍 <b>Location:</b> <b>{html.escape(chosen.label)}</b>\n"
            "🔔 <b>Status:</b> Monitoring is active! You'll receive live pings whenever a room opens up. 🚀",
            parse_mode="HTML",
        )
        return ConversationHandler.END

    return WAITING_FOR_CROUS_INPUT


async def crous_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ <b>CROUS setup cancelled.</b>", parse_mode="HTML")
    return ConversationHandler.END


crous_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("crous", crous_entry)],
    states={
        WAITING_FOR_CROUS_INPUT: [
            CallbackQueryHandler(crous_button_click, pattern="^crous_"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, crous_text_received),
        ],
    },
    fallbacks=[CommandHandler("cancel", crous_cancel)],
    per_message=False,
)
