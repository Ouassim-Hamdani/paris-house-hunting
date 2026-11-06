import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
)

from src.domain.models import ProviderName, Search, SearchCriteria
from src.providers.arpej import ArpejProvider
from src.storage.searches import SearchRepository
from src.storage.users import UserRepository

SELECTING_CITIES = 1
PAGE_SIZE = 8  # 8 cities per keyboard page


def get_db(context: ContextTypes.DEFAULT_TYPE):
    return context.bot_data["db_conn"]


def build_city_keyboard(catalog: list[dict], selected_ids: set[str], page: int) -> InlineKeyboardMarkup:
    """Builds inline keyboard with checkmarks for selected cities and pagination buttons."""
    total_pages = (len(catalog) + PAGE_SIZE - 1) // PAGE_SIZE
    page = max(0, min(page, total_pages - 1))

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    page_items = catalog[start:end]

    buttons = []
    # 2 columns of cities
    for i in range(0, len(page_items), 2):
        row = []
        for item in page_items[i:i+2]:
            cid = item["id"]
            label = item["label"]
            prefix = "✅ " if cid in selected_ids else "⬜ "
            row.append(InlineKeyboardButton(f"{prefix}{label}", callback_data=f"arpej_toggle:{cid}"))
        buttons.append(row)

    # Navigation row
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"arpej_page:{page-1}"))
    nav_row.append(InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="arpej_noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"arpej_page:{page+1}"))
    buttons.append(nav_row)

    # Action row (Save & Cancel)
    buttons.append([
        InlineKeyboardButton(f"💾 Save ({len(selected_ids)} city/cities)", callback_data="arpej_save"),
        InlineKeyboardButton("❌ Cancel", callback_data="arpej_cancel"),
    ])

    return InlineKeyboardMarkup(buttons)


async def arpej_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /arpej."""
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

    provider = ArpejProvider()
    catalog = provider.catalog()
    context.user_data["arpej_catalog"] = catalog

    # Load currently saved cities if any
    search_repo = SearchRepository(conn)
    existing_search = search_repo.get(user.id, ProviderName.ARPEJ)
    selected = set(existing_search.criteria.data.get("cities", [])) if existing_search else set()
    context.user_data["arpej_selected"] = selected
    context.user_data["arpej_page"] = 0

    keyboard = build_city_keyboard(catalog, selected, 0)
    await update.message.reply_text(
        "🏢 <b>ARPEJ City Selection</b> 🏙️✨\n"
        "────────────────────────\n"
        "Tap the cities where you are looking for accommodation to toggle checkmarks (✅ / ⬜).\n"
        "When finished, click <b>💾 Save</b>:\n\n"
        "<i>Send /cancel to abort at any time.</i> ❌",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    return SELECTING_CITIES


async def arpej_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
    selected: set[str] = context.user_data.get("arpej_selected", set())
    catalog: list[dict] = context.user_data.get("arpej_catalog", [])
    page: int = context.user_data.get("arpej_page", 0)

    if data == "arpej_noop":
        return SELECTING_CITIES

    if data == "arpej_cancel":
        await query.edit_message_text("❌ <b>ARPEJ setup cancelled.</b>", parse_mode="HTML")
        return ConversationHandler.END

    if data.startswith("arpej_toggle:"):
        cid = data.split(":", 1)[1]
        if cid in selected:
            selected.remove(cid)
        else:
            selected.add(cid)
        context.user_data["arpej_selected"] = selected

        keyboard = build_city_keyboard(catalog, selected, page)
        await query.edit_message_reply_markup(reply_markup=keyboard)
        return SELECTING_CITIES

    if data.startswith("arpej_page:"):
        new_page = int(data.split(":")[1])
        context.user_data["arpej_page"] = new_page
        keyboard = build_city_keyboard(catalog, selected, new_page)
        await query.edit_message_reply_markup(reply_markup=keyboard)
        return SELECTING_CITIES

    if data == "arpej_save":
        if not selected:
            await query.answer("⚠️ Please check at least one city!", show_alert=True)
            return SELECTING_CITIES

        search_repo = SearchRepository(conn)
        search_repo.save(Search(
            user_id=update.effective_user.id,
            provider=ProviderName.ARPEJ,
            criteria=SearchCriteria({"cities": sorted(list(selected))}),
        ))

        # Format display of saved cities
        city_labels = [c["label"] for c in catalog if c["id"] in selected]
        await query.edit_message_text(
            f"🎉 <b>ARPEJ Target Saved!</b> 🏢✅\n"
            "────────────────────────\n"
            f"🏙️ <b>Monitored Cities ({len(selected)}):</b>\n"
            f"<i>{html.escape(', '.join(city_labels))}</i>\n\n"
            "🔔 <b>Status:</b> Monitoring is active! You'll receive live pings whenever a room becomes available. 🚀",
            parse_mode="HTML",
        )
        return ConversationHandler.END

    return SELECTING_CITIES


async def arpej_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ <b>ARPEJ setup cancelled.</b>", parse_mode="HTML")
    return ConversationHandler.END


arpej_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("arpej", arpej_entry)],
    states={
        SELECTING_CITIES: [
            CallbackQueryHandler(arpej_callback, pattern="^arpej_"),
        ],
    },
    fallbacks=[CommandHandler("cancel", arpej_cancel)],
    per_message=False,
)
