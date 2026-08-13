"""BunaPay Telegram bot — Phase 1.

User flow: /start (hero) → amount/service → quote → wallet → Telebirr
payment → screenshot → request created → admin confirms/completes/rejects.
Guards: blocked users, min/max amount, max pending per user, rate check.
"""

from __future__ import annotations

import functools
import html
import http.server
import json
import logging
import os
import re
import sys
import threading
import urllib.parse
from datetime import datetime, timedelta, time as dtime, timezone
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import db
import messages as m
from config import config

# Windows consoles default to cp1252 and choke on box-drawing chars (─).
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

if config.sentry_enabled:
    import sentry_sdk

    sentry_sdk.init(dsn=config.sentry_dsn, traces_sample_rate=0.1)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger("bunapay")

# ---------- constants ----------

TZ = ZoneInfo("Africa/Addis_Ababa")
ADMIN_ID = config.telegram_admin_id

BSC_WALLET_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
TX_HASH_RE = re.compile(r"^0x[a-fA-F0-9]{16,}$")
NUM_RE = re.compile(r"^\d{1,6}([.,]\d{1,6})?$")

MIN_USDT, MAX_USDT = 5.0, 100.0
MAX_PENDING = 2
SERVICES_PER_PAGE = 4

# conversation states
CUSTOM_AMT, WALLET, WAIT_PAID, SCREENSHOT, TXHASH = range(5)

CB = {
    "CONFIRM": "confirm",
    "CHANGE": "change",
    "PAID": "paid",
    "CANCEL": "cancel",
    "MYREQ": "myreq",
    "HOWTO": "howto",
    "SVC_PICK": "svcpick",
    "SVC_PAGE": "svcpage",
}

# ---------- helpers ----------


def _is_admin(uid: int) -> bool:
    return uid == ADMIN_ID


def _fmt_dt(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso).astimezone(TZ)
        return dt.strftime("%d %b %H:%M")
    except (ValueError, TypeError):
        return "—"


def _short_wallet(w: str) -> str:
    return w[:6] + "…" + w[-4:] if len(w) > 14 else w


def _btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text, callback_data=data)


# ---------- keyboards ----------


def _mini_app_button(rate: float | None) -> InlineKeyboardButton | None:
    """WebApp button that opens the order form; None when MINI_APP_URL unset."""
    if not config.mini_app_url:
        return None
    services = db.list_active_services()
    payload = {
        "r": rate,
        "s": [{"i": s["id"], "n": s["name"], "p": float(s["usdt_price"])} for s in services],
        "min": MIN_USDT,
        "max": MAX_USDT,
    }
    url = f"{config.mini_app_url}?d=" + urllib.parse.quote(
        json.dumps(payload, separators=(",", ":")), safe=""
    )
    return InlineKeyboardButton("Open BunaPay App", web_app=WebAppInfo(url=url))


def hero_keyboard(services: list[dict], page: int = 0) -> InlineKeyboardMarkup:
    rows = [
        [_btn("10 USDT", "amt:10"), _btn("20 USDT", "amt:20")],
        [_btn("50 USDT", "amt:50"), _btn("100 USDT", "amt:100")],
        [_btn("Other amount", "amt:custom")],
    ]
    page_services = services[page * SERVICES_PER_PAGE : (page + 1) * SERVICES_PER_PAGE]
    for i in range(0, len(page_services), 2):
        pair = page_services[i : i + 2]
        rows.append(
            [
                _btn(f"{s['name']} · {float(s['usdt_price']):g}", f"{CB['SVC_PICK']}:{s['id']}:{page}")
                for s in pair
            ]
        )
    nav = []
    if page > 0:
        nav.append(_btn("‹ Back", f"{CB['SVC_PAGE']}:{page - 1}"))
    if (page + 1) * SERVICES_PER_PAGE < len(services):
        nav.append(_btn("More ›", f"{CB['SVC_PAGE']}:{page + 1}"))
    if nav:
        rows.append(nav)
    app_btn = _mini_app_button(db.get_rate())
    if app_btn:
        rows.append([app_btn])
    rows.append([_btn("My requests", CB["MYREQ"]), _btn("How it works", CB["HOWTO"])])
    return InlineKeyboardMarkup(rows)


def quote_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[_btn("Confirm", CB["CONFIRM"]), _btn("Change amount", CB["CHANGE"])]]
    )


def payment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[_btn("I've paid — upload screenshot", CB["PAID"])], [_btn("Cancel", CB["CANCEL"])]]
    )


def single_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[_btn("Cancel", CB["CANCEL"])]])


def admin_keyboard(request_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                _btn("Confirm payment", f"adm:confirm:{request_id}"),
                _btn("Complete", f"adm:complete:{request_id}"),
                _btn("Reject", f"adm:reject:{request_id}"),
            ]
        ]
    )


# ---------- guards ----------


async def _ensure_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """End the conversation if the user has no in-progress flow state."""
    if "amount_usdt" in context.user_data:
        return True
    await update.effective_message.reply_text("Start over with /start")
    return False


def _etb(usdt: float, rate: float) -> float:
    return round(usdt * rate, 2)


def _set_amount(context: ContextTypes.DEFAULT_TYPE, usdt: float, rate: float) -> None:
    context.user_data["amount_usdt"] = usdt
    context.user_data["amount_etb"] = _etb(usdt, rate)


# ---------- user flow ----------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    context.user_data.clear()
    user = db.get_or_create_user(
        uid, update.effective_user.username, update.effective_user.first_name
    )
    if user["is_blocked"]:
        await update.message.reply_text("Your account is blocked. Contact support.")
        return
    rate = db.get_rate()
    services = db.list_active_services()
    await update.message.reply_text(
        m.hero(rate), parse_mode=ParseMode.HTML, reply_markup=hero_keyboard(services)
    )


async def show_quote_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry: amount tile tapped. Shows quote; no state change."""
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    rate = db.get_rate()
    if rate is None:
        await query.edit_message_text("Rates are being updated — try again shortly.")
        return ConversationHandler.END
    usdt = float(query.data.split(":")[1])
    if db.count_pending_for_user(uid) >= MAX_PENDING:
        await query.edit_message_text(
            f"You have {MAX_PENDING} pending orders. Wait for them to finish."
        )
        return ConversationHandler.END
    _set_amount(context, usdt, rate)
    await query.edit_message_text(
        m.quote(usdt, rate, context.user_data["amount_etb"]),
        parse_mode=ParseMode.HTML,
        reply_markup=quote_keyboard(),
    )
    return ConversationHandler.END


async def ask_custom_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry: 'Other amount'. Wait for a number."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"Enter amount in USDT ({MIN_USDT:g}–{MAX_USDT:g}):",
        reply_markup=single_cancel_keyboard(),
    )
    return CUSTOM_AMT


async def custom_amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip().replace(",", ".")
    if not NUM_RE.match(text):
        await update.message.reply_text(
            "Enter a number, e.g. 15", reply_markup=single_cancel_keyboard()
        )
        return CUSTOM_AMT
    usdt = float(text)
    if not (MIN_USDT <= usdt <= MAX_USDT):
        await update.message.reply_text(
            f"Amount must be between {MIN_USDT:g} and {MAX_USDT:g} USDT.",
            reply_markup=single_cancel_keyboard(),
        )
        return CUSTOM_AMT
    rate = db.get_rate()
    if rate is None:
        await update.message.reply_text("Rates are being updated — try again shortly.")
        return ConversationHandler.END
    _set_amount(context, usdt, rate)
    await update.message.reply_text(
        m.quote(usdt, rate, context.user_data["amount_etb"]),
        parse_mode=ParseMode.HTML,
        reply_markup=quote_keyboard(),
    )
    return ConversationHandler.END


async def svc_pick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry: a service tile tapped. Pre-fills the quote with its price."""
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    _, svc_id, page = query.data.split(":")
    rate = db.get_rate()
    if rate is None:
        await query.edit_message_text("Rates are being updated — try again shortly.")
        return ConversationHandler.END
    svc = db.get_service(svc_id)
    if not svc or not svc["active"]:
        await query.edit_message_text("This service is no longer available.")
        return ConversationHandler.END
    if db.count_pending_for_user(uid) >= MAX_PENDING:
        await query.edit_message_text(
            f"You have {MAX_PENDING} pending orders. Wait for them to finish."
        )
        return ConversationHandler.END
    usdt = float(svc["usdt_price"])
    _set_amount(context, usdt, rate)
    await query.edit_message_text(
        m.quote(usdt, rate, context.user_data["amount_etb"]),
        parse_mode=ParseMode.HTML,
        reply_markup=quote_keyboard(),
    )
    return ConversationHandler.END


async def change_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Quote → hero (fresh amounts)."""
    query = update.callback_query
    await query.answer()
    rate = db.get_rate()
    services = db.list_active_services()
    await query.edit_message_text(
        m.hero(rate), parse_mode=ParseMode.HTML, reply_markup=hero_keyboard(services)
    )


async def confirm_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry: Confirm on quote → ask wallet."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Send your BSC (BEP20) wallet address:\n\n<code>0x… (40 hex characters)</code>",
        parse_mode=ParseMode.HTML,
        reply_markup=single_cancel_keyboard(),
    )
    return WALLET


async def wallet_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await _ensure_flow(update, context):
        return ConversationHandler.END
    wallet = update.message.text.strip()
    if not BSC_WALLET_RE.match(wallet):
        await update.message.reply_text(
            "That doesn't look like a valid BSC address. It must be 0x followed by 40 hex characters:",
            reply_markup=single_cancel_keyboard(),
        )
        return WALLET
    context.user_data["wallet"] = wallet
    etb = context.user_data["amount_etb"]
    await update.message.reply_text(
        m.payment_details(etb, config.telebirr_name, config.telebirr_number),
        parse_mode=ParseMode.HTML,
        reply_markup=payment_keyboard(),
    )
    return WAIT_PAID


async def paid_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry: 'I've paid' → ask for screenshot."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Upload your Telebirr payment screenshot:",
        reply_markup=single_cancel_keyboard(),
    )
    return SCREENSHOT


async def screenshot_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await _ensure_flow(update, context):
        return ConversationHandler.END
    file_id = update.message.photo[-1].file_id
    user = db.get_or_create_user(
        update.effective_user.id, update.effective_user.username, update.effective_user.first_name
    )
    req = db.create_request(
        user_id=user["telegram_id"],
        amount_usdt=context.user_data["amount_usdt"],
        amount_etb=context.user_data["amount_etb"],
        wallet_address=context.user_data["wallet"],
        payment_screenshot_file_id=file_id,
    )
    context.user_data.clear()
    await update.message.reply_text(
        m.request_created(req), parse_mode=ParseMode.HTML
    )
    await _notify_admin(update, context, req, user, file_id)
    return ConversationHandler.END


async def _notify_admin(
    update: Update, context: ContextTypes.DEFAULT_TYPE, req: dict, user: dict, file_id: str
) -> None:
    # Photo and card as separate messages: the card is a TEXT message so the
    # admin buttons can be edited (a photo message has no text to edit).
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=file_id)
    caption = (
        m.admin_notification(req, user, _fmt_dt(req["created_at"]))
        + "\n\n" + m.status_line(req["status"])
    )
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=caption,
        parse_mode=ParseMode.HTML,
        reply_markup=admin_keyboard(req["id"]),
    )


# ---------- mini app flow ----------


async def webapp_order_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mini App submit → validate → ask for payment screenshot (then existing flow)."""
    query = update.callback_query
    if not query.web_app_data:
        # No active conversation for app orders — keep the Cancel button working.
        if query.data == CB["CANCEL"] and context.user_data.get("mini_app"):
            await query.answer()
            context.user_data.clear()
            await query.edit_message_text("Cancelled.")
        return
    await query.answer()
    uid = query.from_user.id
    try:
        data = json.loads(query.web_app_data.data)
        usdt = float(data.get("usdt", 0))
        wallet = str(data.get("wallet", "")).strip()
        svc_id = str(data.get("service") or "").strip() or None
    except (ValueError, TypeError, json.JSONDecodeError):
        await context.bot.send_message(uid, "Invalid order data. Please try again in the app.")
        return

    rate = db.get_rate()
    if rate is None:
        await context.bot.send_message(uid, "Rates are being updated — try again shortly.")
        return
    if not (MIN_USDT <= usdt <= MAX_USDT):
        await context.bot.send_message(
            uid, f"Amount must be between {MIN_USDT:g} and {MAX_USDT:g} USDT."
        )
        return
    if not BSC_WALLET_RE.match(wallet):
        await context.bot.send_message(
            uid,
            "That doesn't look like a valid BSC address. It must be 0x followed by 40 hex characters. "
            "Please reopen the app and fix the address.",
        )
        return
    if db.count_pending_for_user(uid) >= MAX_PENDING:
        await context.bot.send_message(
            uid, f"You have {MAX_PENDING} pending orders. Wait for them to finish."
        )
        return
    if svc_id:
        svc = db.get_service(svc_id)
        if not svc or not svc["active"]:
            await context.bot.send_message(uid, "This service is no longer available.")
            return

    _set_amount(context, usdt, rate)
    context.user_data["wallet"] = wallet
    context.user_data["mini_app"] = True
    await context.bot.send_message(
        uid,
        f"Order received — <b>{usdt:g} USDT</b> ≈ <b>{context.user_data['amount_etb']:,.0f} ETB</b>.\n\n"
        "Upload your Telebirr payment screenshot:",
        parse_mode=ParseMode.HTML,
        reply_markup=single_cancel_keyboard(),
    )


async def mini_screenshot_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Screenshot for an order placed via the Mini App (no active conversation)."""
    if "amount_usdt" not in context.user_data or not context.user_data.get("mini_app"):
        return
    file_id = update.message.photo[-1].file_id
    user = db.get_or_create_user(
        update.effective_user.id, update.effective_user.username, update.effective_user.first_name
    )
    req = db.create_request(
        user_id=user["telegram_id"],
        amount_usdt=context.user_data["amount_usdt"],
        amount_etb=context.user_data["amount_etb"],
        wallet_address=context.user_data["wallet"],
        payment_screenshot_file_id=file_id,
    )
    context.user_data.clear()
    await update.message.reply_text(
        m.request_created(req), parse_mode=ParseMode.HTML
    )
    await _notify_admin(update, context, req, user, file_id)


async def my_requests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    reqs = db.list_user_requests(uid)
    await query.edit_message_text(
        m.my_requests(reqs), parse_mode=ParseMode.HTML
    )


async def how_it_works(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(m.how_it_works(), parse_mode=ParseMode.HTML)


async def services_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    page = int(query.data.split(":")[1])
    services = db.list_active_services()
    await query.edit_message_reply_markup(hero_keyboard(services, page))


async def cancel_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text("Cancelled.")
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


# ---------- admin flow ----------


async def admin_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not _is_admin(query.from_user.id):
        await query.answer("Not allowed", show_alert=True)
        return
    req_id = query.data.split(":", 2)[2]
    req = db.update_request(
        req_id, status="paid", paid_at=datetime.now(timezone.utc).isoformat()
    )
    if not req:
        await query.edit_message_text("Request not found.")
        return
    await query.edit_message_text(m.admin_request_update(req), parse_mode=ParseMode.HTML)
    await context.bot.send_message(
        req["user_id"],
        f"Payment confirmed for <b>{req_id}</b>. Your USDT will be sent shortly.",
        parse_mode=ParseMode.HTML,
    )


async def admin_complete_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry: Complete → ask TX hash."""
    query = update.callback_query
    await query.answer()
    if not _is_admin(query.from_user.id):
        await query.answer("Not allowed", show_alert=True)
        return ConversationHandler.END
    context.user_data["complete_req_id"] = query.data.split(":", 2)[2]
    await query.edit_message_text(
        "Send the BSC transaction hash:\n\n<code>0x… (16+ hex characters)</code>",
        parse_mode=ParseMode.HTML,
    )
    return TXHASH


async def txhash_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    req_id = context.user_data.get("complete_req_id")
    if not req_id:
        await update.message.reply_text("No pending action. Use /start.")
        return ConversationHandler.END
    tx = update.message.text.strip()
    if not TX_HASH_RE.match(tx):
        await update.message.reply_text(
            "Invalid transaction hash — must start with 0x followed by at least 16 hex characters:"
        )
        return TXHASH
    req = db.update_request(
        req_id,
        status="completed",
        tx_hash=tx,
        completed_at=datetime.now(timezone.utc).isoformat(),
    )
    context.user_data.clear()
    if not req:
        await update.message.reply_text("Request not found.")
        return ConversationHandler.END
    db.bump_user_stats(req["user_id"], float(req["amount_etb"]))
    await update.message.reply_text(
        m.admin_request_update(req), parse_mode=ParseMode.HTML
    )
    await context.bot.send_message(
        req["user_id"],
        f"USDT sent for <b>{req_id}</b>.\n"
        f"TX: <code>{tx}</code>\nThank you for using BunaPay!",
        parse_mode=ParseMode.HTML,
    )
    return ConversationHandler.END


async def admin_reject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not _is_admin(query.from_user.id):
        await query.answer("Not allowed", show_alert=True)
        return
    req_id = query.data.split(":", 2)[2]
    req = db.update_request(req_id, status="rejected")
    if not req:
        await query.edit_message_text("Request not found.")
        return
    await query.edit_message_text(m.admin_request_update(req), parse_mode=ParseMode.HTML)
    await context.bot.send_message(
        req["user_id"],
        f"Request <b>{req_id}</b> was rejected. Contact support if you believe this is a mistake.",
        parse_mode=ParseMode.HTML,
    )


# ---------- admin commands ----------


async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        return
    reqs = db.list_pending()
    if not reqs:
        await update.message.reply_text("No pending requests.")
        return
    for r in reqs:
        text = (
            f"<b>{r['id']}</b> · {float(r['amount_usdt']):g} USDT · "
            f"{float(r['amount_etb']):,.0f} ETB · <b>{r['status'].upper()}</b>"
        )
        await update.message.reply_text(
            text, parse_mode=ParseMode.HTML, reply_markup=admin_keyboard(r["id"])
        )


async def set_rate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        return
    try:
        rate = float(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /set_rate <value>")
        return
    if rate <= 0:
        await update.message.reply_text("Rate must be positive.")
        return
    db.set_rate(rate, update.effective_user.id)
    await update.message.reply_text(m.rate_updated(rate), parse_mode=ParseMode.HTML)


async def set_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        return
    # /set_service <id> <name> <usdt_price> [active:1/0]
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "Usage: /set_service <id> <name> <usdt_price> [active=1]"
        )
        return
    svc_id, name, price_str = args[0], args[1], args[2]
    active = True
    if len(args) >= 4 and args[3] == "0":
        active = False
    try:
        price = float(price_str)
    except ValueError:
        await update.message.reply_text("Invalid USDT price.")
        return
    rate = db.get_rate() or 110.0
    svc = db.upsert_service(
        {
            "id": svc_id.lower(),
            "name": name,
            "usdt_price": price,
            "etb_price": round(price * rate, 2),
            "active": active,
        }
    )
    await update.message.reply_text(m.service_updated(svc), parse_mode=ParseMode.HTML)


async def _user_flag(update: Update, context: ContextTypes.DEFAULT_TYPE, flag: str) -> None:
    if not _is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Usage: /%s <telegram_id or @username>" % flag)
        return
    raw = context.args[0]
    if raw.lstrip("-").isdigit():
        target = int(raw)
        db.set_user_blocked(target, flag in ("block_user",)) if flag.startswith("block") \
            else db.set_user_trusted(target, flag in ("add_trusted",))
        name = raw
    else:
        username = raw.lstrip("@")
        user = db.get_user_by_username(username)
        if not user:
            await update.message.reply_text(f"User @{username} not found.")
            return
        target = user["telegram_id"]
        if flag.startswith("block"):
            db.set_user_blocked(target, flag == "block_user")
        else:
            db.set_user_trusted(target, flag == "add_trusted")
        name = f"@{username}"
    action = {
        "block_user": "blocked",
        "unblock_user": "unblocked",
        "add_trusted": "trusted",
        "remove_trusted": "untrusted",
    }[flag]
    await update.message.reply_text(f"{name} {action}.")


async def trusted_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        return
    users = db.list_trusted_users()
    if not users:
        await update.message.reply_text("No trusted users yet.")
        return
    lines = ["<b>TRUSTED USERS</b>", ""]
    lines += [f"@{u['username'] or u['telegram_id']} ({u['telegram_id']})" for u in users]
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


# ---------- jobs ----------


async def expiry_sweep(context: ContextTypes.DEFAULT_TYPE) -> None:
    expired = db.list_expired_candidates(hours=12)
    for req in expired:
        db.update_request(req["id"], status="expired")
        try:
            await context.bot.send_message(
                req["user_id"],
                f"Request <b>{req['id']}</b> expired (no payment within 12h). "
                "You can start a new one anytime.",
                parse_mode=ParseMode.HTML,
            )
        except Exception:  # noqa: BLE001
            logger.exception("expiry notify failed for %s", req["id"])
    if expired:
        await context.bot.send_message(
            ADMIN_ID, f"{len(expired)} request(s) expired.", parse_mode=ParseMode.HTML
        )


async def daily_stats(context: ContextTypes.DEFAULT_TYPE) -> None:
    since = datetime.now(TZ) - timedelta(days=1)
    reqs = db.list_requests_since(since)
    counts = {
        "new": len(reqs),
        "pending": sum(1 for r in reqs if r["status"] == "pending"),
        "completed": sum(1 for r in reqs if r["status"] == "completed"),
        "rejected": sum(1 for r in reqs if r["status"] == "rejected"),
        "etb": sum(float(r["amount_etb"]) for r in reqs if r["status"] == "completed"),
    }
    await context.bot.send_message(ADMIN_ID, m.daily_stats(counts), parse_mode=ParseMode.HTML)


# ---------- errors ----------


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled error while processing update")
    if config.sentry_enabled:
        if isinstance(update, Update) and update.effective_user:
            sentry_sdk.get_current_scope().set_user(
                {
                    "id": str(update.effective_user.id),
                    "username": update.effective_user.username,
                }
            )
        sentry_sdk.capture_exception(context.error, extra={"update": repr(update)})
    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text("Something went wrong. Please try /start.")
    except Exception:  # noqa: BLE001
        pass


# ---------- app ----------


def build_app() -> Application:
    app = (
        ApplicationBuilder()
        .token(config.telegram_bot_token)
        .post_init(post_init)
        .build()
    )

    user_flow = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(show_quote_amount, pattern=r"^amt:\d+$"),
            CallbackQueryHandler(ask_custom_amount, pattern=r"^amt:custom$"),
            CallbackQueryHandler(svc_pick, pattern=rf"^{CB['SVC_PICK']}:"),
            CallbackQueryHandler(confirm_pressed, pattern=f"^{CB['CONFIRM']}$"),
            CallbackQueryHandler(paid_pressed, pattern=f"^{CB['PAID']}$"),
        ],
        states={
            CUSTOM_AMT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, custom_amount_received)
            ],
            WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, wallet_received)],
            WAIT_PAID: [
                CallbackQueryHandler(paid_pressed, pattern=f"^{CB['PAID']}$"),
                CallbackQueryHandler(cancel_pressed, pattern=f"^{CB['CANCEL']}$"),
            ],
            SCREENSHOT: [MessageHandler(filters.PHOTO, screenshot_received)],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_pressed, pattern=f"^{CB['CANCEL']}$"),
            CommandHandler("cancel", cancel_command),
        ],
    )

    admin_flow = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_complete_pressed, pattern=r"^adm:complete:")],
        states={TXHASH: [MessageHandler(filters.TEXT & ~filters.COMMAND, txhash_received)]},
        fallbacks=[CommandHandler("cancel", cancel_command)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dashboard", dashboard))
    app.add_handler(CommandHandler("set_rate", set_rate))
    app.add_handler(CommandHandler("set_service", set_service))
    app.add_handler(CommandHandler("trusted_list", trusted_list))
    for flag in ("block_user", "unblock_user", "add_trusted", "remove_trusted"):
        app.add_handler(CommandHandler(flag, lambda u, c, f=flag: _user_flag(u, c, f)))
    app.add_handler(user_flow)
    app.add_handler(admin_flow)
    app.add_handler(CallbackQueryHandler(change_amount, pattern=f"^{CB['CHANGE']}$"))
    app.add_handler(CallbackQueryHandler(my_requests, pattern=f"^{CB['MYREQ']}$"))
    app.add_handler(CallbackQueryHandler(how_it_works, pattern=f"^{CB['HOWTO']}$"))
    app.add_handler(CallbackQueryHandler(services_page, pattern=rf"^{CB['SVC_PAGE']}:\d+$"))
    app.add_handler(CallbackQueryHandler(admin_confirm, pattern=r"^adm:confirm:"))
    app.add_handler(CallbackQueryHandler(admin_reject, pattern=r"^adm:reject:"))
    # Mini App: web_app_data callbacks carry no data, so this must be the last
    # callback handler (it only fires for queries no pattern matched above).
    app.add_handler(CallbackQueryHandler(webapp_order_received))
    app.add_handler(MessageHandler(filters.PHOTO, mini_screenshot_received))
    app.add_error_handler(error_handler)
    return app


async def post_init(app: Application) -> None:
    jq = app.job_queue
    jq.run_repeating(expiry_sweep, interval=timedelta(minutes=10), first=30)
    jq.run_daily(daily_stats, time=dtime(hour=23, minute=45, tzinfo=TZ), days=tuple(range(7)))
    logger.info("Bot started. Jobs scheduled: 12h expiry sweep + daily stats.")


# ---------- mini app static server ----------


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A002 - keep request logs off stdout
        pass


def start_static_server() -> None:
    """Serve the webapp/ Mini App so one Railway service hosts bot + web app.

    Uses PORT (Railway's public-networking port, default 3000). No-op locally
    or when webapp/ is missing, so local dev keeps working unchanged.
    """
    webapp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webapp")
    if not os.path.isdir(webapp_dir):
        logger.info("webapp/ not found — skipping static server")
        return
    port = int(os.environ.get("PORT", "3000"))
    handler = functools.partial(_QuietHandler, directory=webapp_dir)
    server = http.server.ThreadingHTTPServer(("0.0.0.0", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logger.info("Mini App web server listening on port %s", port)


def main() -> None:
    start_static_server()
    app = build_app()
    logger.info("Starting BunaPay bot (polling)")
    app.run_polling()


if __name__ == "__main__":
    main()
