import logging
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from config import API_ID, API_HASH, SESSION_STRING
from database import get_keywords, get_monitored_groups, get_setting

logger = logging.getLogger(__name__)

userbot = Client(
    name="userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
)


def _msg_link(chat_id: int, msg_id: int) -> str:
    cid = str(chat_id)
    pure = cid[4:] if cid.startswith("-100") else cid.lstrip("-")
    return f"https://t.me/c/{pure}/{msg_id}"


def _build_text(message: Message) -> str:
    user = message.from_user
    chat = message.chat
    raw_text = (message.text or message.caption or "").strip()

    # ── Sender ────────────────────────────────────────────────────────────────
    if user:
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Noma'lum"
        profile_url = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user.id}"
        name_link = f"[{full_name}]({profile_url})"
        username_line = f"👤 **Username:** @{user.username}\n" if user.username else ""
        user_id_val = user.id
    else:
        name_link = "Noma'lum"
        username_line = ""
        user_id_val = "?"

    # ── Message link ──────────────────────────────────────────────────────────
    link = _msg_link(chat.id, message.id)
    short = raw_text[:180] + ("…" if len(raw_text) > 180 else "")
    text_link = f"[{short}]({link})" if short else f"[Xabar]({link})"

    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    return (
        f"🚖 **Yangi Zakaz!**\n"
        f"{'─' * 28}\n"
        f"👤 **Ismi:** {name_link}\n"
        f"💬 **Xabar:** {text_link}\n"
        f"{username_line}"
        f"🆔 **Chat ID:** `{chat.id}`\n"
        f"👤 **User ID:** `{user_id_val}`\n"
        f"📍 **Guruh:** {chat.title or 'Noma\\'lum'}\n"
        f"🕐 **Vaqt:** {now}"
    )


@userbot.on_message(filters.group & ~filters.bot)
async def on_group_message(client: Client, message: Message):
    raw = (message.text or message.caption or "").strip().lower()
    if not raw:
        return

    # Filter by monitored groups if any are configured
    monitored = await get_monitored_groups()
    if monitored and message.chat.id not in {g[0] for g in monitored}:
        return

    keywords = await get_keywords()
    if not keywords or not any(kw in raw for kw in keywords):
        return

    orders_group = await get_setting("orders_group_id")
    if not orders_group:
        logger.warning("orders_group_id is not set — skipping forward")
        return

    try:
        await client.send_message(
            int(orders_group),
            _build_text(message),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        logger.info("Order forwarded from chat %s msg %s", message.chat.id, message.id)
    except Exception as exc:
        logger.error("Failed to forward order: %s", exc)
