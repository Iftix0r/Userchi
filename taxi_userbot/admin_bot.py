from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import ADMIN_IDS, BOT_TOKEN
from pyrogram.enums import ChatType

from userbot import invalidate_cache, userbot
from database import (
    add_keyword,
    add_monitored_group,
    delete_keyword,
    get_keywords,
    get_monitored_groups,
    get_setting,
    remove_monitored_group,
    set_setting,
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ── FSM States ────────────────────────────────────────────────────────────────

class AddKeyword(StatesGroup):
    waiting = State()



class SetOrdersGroup(StatesGroup):
    waiting = State()


# ── Helpers ───────────────────────────────────────────────────────────────────

def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS


def main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔑 Kalit So'zlar", callback_data="keywords"),
            InlineKeyboardButton(text="👥 Guruhlar",      callback_data="groups"),
        ],
        [
            InlineKeyboardButton(text="📤 Zakaz Guruhi",  callback_data="orders_group"),
            InlineKeyboardButton(text="📊 Statistika",    callback_data="stats"),
        ],
    ])


def back_kb(cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data=cb)]
    ])


async def _edit(cb: CallbackQuery, text: str, kb: InlineKeyboardMarkup):
    await cb.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")


# ── /start ────────────────────────────────────────────────────────────────────

@dp.message(CommandStart())
async def cmd_start(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("❌ Ruxsat yo'q!")
        return
    await msg.answer(
        "🚖 *Taxi Userbot — Admin Panel*\n\nMenyuni tanlang:",
        reply_markup=main_kb(),
        parse_mode="Markdown",
    )


# ── Main menu callback ────────────────────────────────────────────────────────

@dp.callback_query(F.data == "main_menu")
async def cb_main_menu(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        return
    await state.clear()
    await _edit(cb, "🚖 *Taxi Userbot — Admin Panel*\n\nMenyuni tanlang:", main_kb())


# ── Keywords ──────────────────────────────────────────────────────────────────

@dp.callback_query(F.data == "keywords")
async def cb_keywords(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    kws = await get_keywords()
    body = "\n".join(f"• `{k}`" for k in kws) if kws else "_Hali kalit so'z yo'q._"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Qo'shish",  callback_data="add_keyword"),
            InlineKeyboardButton(text="🗑 O'chirish", callback_data="del_keyword_list"),
        ],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="main_menu")],
    ])
    await _edit(cb, f"🔑 *Kalit So'zlar ({len(kws)} ta):*\n\n{body}", kb)


@dp.callback_query(F.data == "add_keyword")
async def cb_add_keyword_start(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        return
    await state.set_state(AddKeyword.waiting)
    await _edit(
        cb,
        "🔑 Kalit so'z(lar)ni yozing:\n\n"
        "_(bitta: `taksi`)\n"
        "(bir nechta: `taksi, taxi, haydovchi`)_",
        back_kb("keywords"),
    )


@dp.message(AddKeyword.waiting)
async def msg_add_keyword(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    words = [w.strip().lower() for w in msg.text.split(",") if w.strip()]
    if not words:
        await msg.answer("❌ Bo'sh bo'lmaydi!")
        return
    added, exists = [], []
    for kw in words:
        ok = await add_keyword(kw, msg.from_user.id)
        (added if ok else exists).append(kw)
    if added:
        invalidate_cache()
    await state.clear()
    lines = []
    if added:
        lines.append("✅ Qo'shildi: " + ", ".join(f"`{k}`" for k in added))
    if exists:
        lines.append("⚠️ Allaqachon mavjud: " + ", ".join(f"`{k}`" for k in exists))
    await msg.answer("\n".join(lines), reply_markup=main_kb(), parse_mode="Markdown")


@dp.callback_query(F.data == "del_keyword_list")
async def cb_del_keyword_list(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    kws = await get_keywords()
    if not kws:
        await cb.answer("Kalit so'zlar yo'q!", show_alert=True)
        return
    buttons = [[InlineKeyboardButton(text=f"🗑 {k}", callback_data=f"delkw_{k}")] for k in kws]
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="keywords")])
    await _edit(cb, "🗑 O'chirish uchun kalit so'zni tanlang:", InlineKeyboardMarkup(inline_keyboard=buttons))


@dp.callback_query(F.data.startswith("delkw_"))
async def cb_del_keyword(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    kw = cb.data[6:]
    ok = await delete_keyword(kw)
    if ok:
        invalidate_cache()
    await cb.answer(f"✅ '{kw}' o'chirildi!" if ok else "❌ Topilmadi!", show_alert=not ok)
    await cb_del_keyword_list(cb)


# ── Monitored groups ──────────────────────────────────────────────────────────

@dp.callback_query(F.data == "groups")
async def cb_groups(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    groups = await get_monitored_groups()
    if groups:
        unknown = "Noma'lum"
        body = "\n".join(f"• {g[1] or unknown}: `{g[0]}`" for g in groups)
    else:
        body = "_Guruh qo'shilmagan — barcha guruhlar kuzatiladi._"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Qo'shish",  callback_data="add_group"),
            InlineKeyboardButton(text="🗑 O'chirish", callback_data="del_group_list"),
        ],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="main_menu")],
    ])
    await _edit(cb, f"👥 *Kuzatiladigan Guruhlar ({len(groups)} ta):*\n\n{body}", kb)


async def _show_group_picker(cb: CallbackQuery):
    await cb.message.edit_text("⏳ Guruhlar yuklanmoqda...")
    monitored = {g[0] for g in await get_monitored_groups()}
    buttons = []
    async for dialog in userbot.get_dialogs():
        chat = dialog.chat
        if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
            continue
        icon = "✅" if chat.id in monitored else "➕"
        buttons.append([InlineKeyboardButton(
            text=f"{icon} {chat.title}",
            callback_data=f"addgrp_{chat.id}",
        )])
    if not buttons:
        await cb.message.edit_text(
            "❌ Userbot hech qanday guruhda emas.",
            reply_markup=back_kb("groups"),
            parse_mode="Markdown",
        )
        return
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="groups")])
    await cb.message.edit_text(
        "👥 Kuzatish uchun guruhni tanlang:\n_✅ — allaqachon qo'shilgan_",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown",
    )


@dp.callback_query(F.data == "add_group")
async def cb_add_group_start(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        return
    await state.clear()
    await _show_group_picker(cb)


@dp.callback_query(F.data.startswith("addgrp_"))
async def cb_addgrp_select(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    gid = int(cb.data[7:])
    chat = await userbot.get_chat(gid)
    title = chat.title or f"Guruh {gid}"
    ok = await add_monitored_group(gid, title, cb.from_user.id)
    if ok:
        invalidate_cache()
    await cb.answer(
        f"✅ '{title}' qo'shildi!" if ok else f"⚠️ '{title}' allaqachon mavjud!",
        show_alert=True,
    )
    await _show_group_picker(cb)


@dp.callback_query(F.data == "del_group_list")
async def cb_del_group_list(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    groups = await get_monitored_groups()
    if not groups:
        await cb.answer("Guruhlar yo'q!", show_alert=True)
        return
    buttons = [
        [InlineKeyboardButton(text=f"🗑 {g[1] or g[0]} ({g[0]})", callback_data=f"delgrp_{g[0]}")]
        for g in groups
    ]
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="groups")])
    await _edit(cb, "🗑 O'chirish uchun guruhni tanlang:", InlineKeyboardMarkup(inline_keyboard=buttons))


@dp.callback_query(F.data.startswith("delgrp_"))
async def cb_del_group(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    gid = int(cb.data[7:])
    ok = await remove_monitored_group(gid)
    if ok:
        invalidate_cache()
    await cb.answer(f"✅ Guruh o'chirildi!" if ok else "❌ Topilmadi!", show_alert=not ok)
    await cb_del_group_list(cb)


# ── Orders group ──────────────────────────────────────────────────────────────

@dp.callback_query(F.data == "orders_group")
async def cb_orders_group(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    current = await get_setting("orders_group_id")
    val = f"`{current}`" if current else "❌ O'rnatilmagan"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ O'zgartirish", callback_data="set_orders_group")],
        [InlineKeyboardButton(text="🔙 Orqaga",       callback_data="main_menu")],
    ])
    await _edit(cb, f"📤 *Zakaz Guruhi:*\n\nHozirgi: {val}", kb)


@dp.callback_query(F.data == "set_orders_group")
async def cb_set_orders_group_start(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        return
    await state.set_state(SetOrdersGroup.waiting)
    await _edit(
        cb,
        "📤 Zakazlar yuboriladigan guruh ID sini yozing:\n\n_(masalan: `-1001234567890`)_",
        back_kb("orders_group"),
    )


@dp.message(SetOrdersGroup.waiting)
async def msg_set_orders_group(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    try:
        gid = int(msg.text.strip())
    except ValueError:
        await msg.answer("❌ Noto'g'ri format!")
        return
    await set_setting("orders_group_id", str(gid))
    await state.clear()
    await msg.answer(
        f"✅ Zakaz guruhi `{gid}` ga o'rnatildi!",
        reply_markup=main_kb(),
        parse_mode="Markdown",
    )


# ── Stats ─────────────────────────────────────────────────────────────────────

@dp.callback_query(F.data == "stats")
async def cb_stats(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    kws = await get_keywords()
    groups = await get_monitored_groups()
    orders = await get_setting("orders_group_id", "O'rnatilmagan")
    text = (
        f"📊 *Statistika:*\n\n"
        f"🔑 Kalit so'zlar: *{len(kws)} ta*\n"
        f"👥 Kuzatiladigan guruhlar: *{len(groups)} ta*\n"
        f"📤 Zakaz guruhi: `{orders}`\n\n"
        f"🤖 Userbot: *Ishlayapti* ✅"
    )
    await _edit(cb, text, back_kb("main_menu"))
