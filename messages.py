"""BunaPay message composer — Apple-style HTML sections.

Telegram HTML has no colors, backgrounds, borders or CSS, so the Apple
look is built from: CAPS labels, bold values, monospace (``<code>``)
aligned rows and ``─`` rules. No emoji anywhere.
"""

from __future__ import annotations

_RULE = "─" * 22


def _pad(label: str, width: int = 9) -> str:
    return label.ljust(width)


def hero(rate: float | None) -> str:
    """First screen — straight to work: rate card + pay path."""
    if rate is None:
        return (
            "<b>BunaPay</b>\n\n"
            "RATE UNAVAILABLE\n"
            "We're updating our rates. Check back in a bit."
        )
    return (
        "<b>BunaPay</b>\n\n"
        "CURRENT RATE\n"
        f"<b>1 USDT = {rate:g} ETB</b>\n\n"
        f"{_RULE}\n"
        "TELEBIRR  →  BSC BEP20  →  WE CONFIRM\n"
        f"{_RULE}\n\n"
        "Buy USDT in minutes. Pay with Telebirr, receive on your BSC wallet."
    )


def quote(usdt: float, rate: float, etb: float) -> str:
    """iOS-style quote rows (monospace so the columns align)."""
    return (
        "<b>YOUR QUOTE</b>\n\n"
        f"<code>{_pad('USDT')}{usdt:g}\n"
        f"{_pad('Rate')}{rate:g} ETB\n"
        f"{'─' * 18}\n"
        f"{_pad('Total')}{etb:,.0f} ETB</code>\n\n"
        "Confirm to continue?"
    )


def service_price(name: str, usdt: float, etb: float) -> str:
    return (
        f"<b>{name}</b> — {usdt:g} USDT\n\n"
        f"<code>{_pad('USDT')}{usdt:g}\n"
        f"{_pad('ETB')}{etb:,.0f}</code>\n\n"
        "Get USDT for this subscription?"
    )


def payment_details(etb: float, name: str, number: str) -> str:
    return (
        "<b>PAY VIA TELEBIRR</b>\n\n"
        f"<code>{_pad('Account', 9)}{name}\n"
        f"{_pad('Number', 9)}{number}\n"
        f"{_pad('Amount', 9)}{etb:,.0f} ETB</code>\n\n"
        "After paying, tap the button below and upload your screenshot."
    )


def request_created(req: dict) -> str:
    return (
        "<b>REQUEST CREATED</b>\n\n"
        f"<code>{_pad('ID')}{req['id']}\n"
        f"{_pad('USDT')}{float(req['amount_usdt']):g}\n"
        f"{_pad('Total')}{float(req['amount_etb']):,.0f} ETB\n"
        f"{_pad('Wallet')}{_short_wallet(req['wallet_address'])}</code>\n\n"
        "STATUS: <b>PENDING</b>\n"
        "We'll verify your payment and send USDT to your wallet. "
        "You'll be notified at every step."
    )


def status_line(status: str) -> str:
    return f"STATUS: <b>{status.upper()}</b>"


def request_card(req: dict) -> str:
    """Compact request summary used in My Requests."""
    return (
        f"{req['id']} · {float(req['amount_usdt']):g} USDT · "
        f"{float(req['amount_etb']):,.0f} ETB\n"
        f"STATUS: <b>{req['status'].upper()}</b>"
    )


def my_requests(reqs: list[dict]) -> str:
    if not reqs:
        return "<b>YOUR REQUESTS</b>\n\nNo requests yet. Pick an amount to get started."
    body = "\n\n".join(request_card(r) for r in reqs)
    return "<b>YOUR REQUESTS</b>\n\n" + body


def how_it_works() -> str:
    return (
        "<b>HOW IT WORKS</b>\n\n"
        "1. Pick an amount (or a subscription)\n"
        "2. Pay via Telebirr — account details shown\n"
        "3. Upload your payment screenshot\n"
        "4. We verify and send USDT to your BSC (BEP20) wallet\n\n"
        "Min 5 USDT · Max 100 USDT · 2 pending orders at a time"
    )


def admin_notification(req: dict, user: dict, created: str | None = None) -> str:
    wallet = req["wallet_address"]
    line = (
        f"<b>NEW REQUEST {req['id']}</b>\n"
        f"User: {user.get('first_name') or '—'} (@{user.get('username') or '—'})\n"
    )
    if created:
        line += f"Created: {created}\n"
    line += (
        f"\n<code>{_pad('USDT')}{float(req['amount_usdt']):g}\n"
        f"{_pad('Total')}{float(req['amount_etb']):,.0f} ETB\n"
        f"{_pad('Wallet')}{_short_wallet(wallet)}</code>"
    )
    return line


def admin_request_update(req: dict) -> str:
    return (
        f"<b>{req['id']}</b> · {float(req['amount_usdt']):g} USDT · "
        f"{float(req['amount_etb']):,.0f} ETB\n"
        f"STATUS: <b>{req['status'].upper()}</b>"
    )


def daily_stats(counts: dict) -> str:
    return (
        "<b>DAILY STATS</b>\n\n"
        f"New requests: <b>{counts['new']}</b>\n"
        f"Pending: <b>{counts['pending']}</b>\n"
        f"Completed: <b>{counts['completed']}</b>\n"
        f"Rejected: <b>{counts['rejected']}</b>\n"
        f"ETB volume: <b>{counts['etb']:,.0f} ETB</b>"
    )


def rate_updated(rate: float) -> str:
    return f"Rate updated: <b>1 USDT = {rate:g} ETB</b>"


def service_updated(service: dict) -> str:
    return (
        f"Service <b>{service['name']}</b> ({service['id']}) — "
        f"{float(service['usdt_price']):g} USDT · active={bool(service['active'])}"
    )


def _short_wallet(wallet: str) -> str:
    if len(wallet) <= 14:
        return wallet
    return f"{wallet[:6]}…{wallet[-4:]}"
