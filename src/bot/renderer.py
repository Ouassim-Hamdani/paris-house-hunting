import html
from src.domain.models import Offer, ProviderName


def format_offer_html(offer: Offer) -> str:
    """Formats an Offer into a safe HTML card for Telegram messages."""
    provider_icon = "🎓" if offer.provider == ProviderName.CROUS else "🏢"
    provider_name = offer.provider.value.upper()
    title_escaped = html.escape(offer.name)

    lines = [
        f"🚨 <b>HOUSING AVAILABLE!</b> 🏠✨",
        "────────────────────────",
        f"🏢 <b>Source:</b> {provider_icon} <b>{provider_name}</b>",
        f"🏠 <b>Residence:</b> <b>{title_escaped}</b>",
    ]

    # Location
    loc_parts = []
    if offer.city:
        loc_parts.append(html.escape(offer.city))
    if offer.postcode:
        loc_parts.append(f"({html.escape(offer.postcode)})")
    if loc_parts:
        lines.append(f"📍 <b>Location:</b> {' '.join(loc_parts)}")

    if offer.address:
        lines.append(f"🗺️ <b>Address:</b> <i>{html.escape(offer.address)}</i>")

    # Price & size
    if offer.price:
        lines.append(f"💰 <b>Price:</b> {html.escape(offer.price)}")
    if offer.size:
        lines.append(f"📐 <b>Size:</b> {html.escape(offer.size)}")

    lines.append("────────────────────────")

    # Link
    if offer.url:
        lines.append(f'🌐 <b>Reserve it here:</b> 👉 <a href="{html.escape(offer.url)}">Click to View & Apply</a> 🚀')

    return "\n".join(lines)


async def send_offer_notification(bot, user_id: int, offer: Offer) -> bool:
    """Sends the offer card to a Telegram user. Sends as photo with caption if image_url exists."""
    text = format_offer_html(offer)
    try:
        if offer.image_url:
            try:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=offer.image_url,
                    caption=text,
                    parse_mode="HTML",
                )
                return True
            except Exception:
                # Fallback to plain text message if image loading fails
                pass

        await bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=False,
        )
        return True
    except Exception as e:
        # User blocked the bot or network failure
        return False
