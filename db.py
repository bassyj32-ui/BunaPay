"""BunaPay Supabase data layer.

All queries use the service-role key (server-side only, never client).
supabase-py returns rows as plain dicts.
"""

from datetime import datetime, timedelta, timezone
from time import monotonic
from typing import Any

from supabase import Client, create_client

from config import config

client: Client = create_client(config.supabase_url, config.supabase_service_key)

REQUEST_STATUSES = ("pending", "paid", "completed", "cancelled", "rejected", "expired")

# Short-TTL in-memory caches: rate and services are read on nearly every
# interaction but change rarely. Saves a Supabase round trip per button press.
_RATE_TTL = 30.0
_SVC_TTL = 60.0
_RATE_CACHE: dict = {"t": 0.0, "v": None}
_SVC_CACHE: dict = {"t": 0.0, "v": None}


def _fresh(cache: dict, ttl: float) -> bool:
    return monotonic() - cache["t"] < ttl

# ---------- users ----------


def get_or_create_user(telegram_id: int, username: str | None, first_name: str | None) -> dict:
    """Fetch a user, creating the row on first contact (upsert returns the row)."""
    rows = (
        client.table("users")
        .upsert(
            {"telegram_id": telegram_id, "username": username, "first_name": first_name},
            on_conflict="telegram_id",
        )
        .execute()
        .data
    )
    return rows[0]


def get_user(telegram_id: int) -> dict | None:
    rows = client.table("users").select("*").eq("telegram_id", telegram_id).execute().data
    return rows[0] if rows else None


def set_user_blocked(telegram_id: int, blocked: bool) -> None:
    client.table("users").update({"is_blocked": blocked}).eq("telegram_id", telegram_id).execute()


def set_user_trusted(telegram_id: int, trusted: bool) -> None:
    client.table("users").update({"is_trusted": trusted}).eq("telegram_id", telegram_id).execute()


def get_user_by_username(username: str) -> dict | None:
    rows = (
        client.table("users")
        .select("*")
        .eq("username", username)
        .limit(1)
        .execute()
        .data
    )
    return rows[0] if rows else None


def list_trusted_users() -> list[dict]:
    return (
        client.table("users")
        .select("telegram_id, username, first_name, created_at")
        .eq("is_trusted", True)
        .order("created_at")
        .execute()
        .data
    )


def bump_user_stats(telegram_id: int, etb: float) -> None:
    """Increment total_requests / total_spent_etb after a completed trade.

    Done via RPC so the increment is atomic (no read-modify-write race).
    """
    client.rpc(
        "bump_user_stats",
        {"p_telegram_id": telegram_id, "p_etb": float(etb)},
    ).execute()


# ---------- rate ----------


def get_rate() -> float | None:
    """Current USDT->ETB rate (most recent rate_settings row), TTL-cached."""
    if _fresh(_RATE_CACHE, _RATE_TTL):
        return _RATE_CACHE["v"]
    rows = (
        client.table("rate_settings")
        .select("*")
        .order("id", desc=True)
        .limit(1)
        .execute()
        .data
    )
    rate = float(rows[0]["usdt_to_etb"]) if rows else None
    _RATE_CACHE.update(t=monotonic(), v=rate)
    return rate


def set_rate(usdt_to_etb: float, updated_by: int) -> float:
    """Insert a new rate row; returns the stored rate."""
    rows = (
        client.table("rate_settings")
        .insert({"usdt_to_etb": float(usdt_to_etb), "updated_by": updated_by})
        .execute()
        .data
    )
    _RATE_CACHE.update(t=0.0, v=None)  # invalidate
    return float(rows[0]["usdt_to_etb"])


# ---------- requests ----------


def create_request(
    user_id: int,
    amount_usdt: float,
    amount_etb: float,
    wallet_address: str,
    payment_screenshot_file_id: str | None = None,
) -> dict:
    rows = (
        client.table("requests")
        .insert(
            {
                "user_id": user_id,
                "amount_usdt": float(amount_usdt),
                "amount_etb": float(amount_etb),
                "wallet_address": wallet_address,
                "payment_screenshot_file_id": payment_screenshot_file_id,
            }
        )
        .execute()
        .data
    )
    return rows[0]


def get_request(request_id: str) -> dict | None:
    rows = client.table("requests").select("*").eq("id", request_id).execute().data
    return rows[0] if rows else None


def update_request(request_id: str, **fields: Any) -> dict | None:
    """Update a request (status, tx_hash, timestamps, notes...)."""
    rows = (
        client.table("requests").update(fields).eq("id", request_id).execute().data
    )
    return rows[0] if rows else None


def count_pending_for_user(user_id: int) -> int:
    rows = (
        client.table("requests")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .in_("status", ("pending", "paid"))
        .execute()
    )
    return int(rows.count or 0)


def list_user_requests(user_id: int, limit: int = 10) -> list[dict]:
    return (
        client.table("requests")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
        .data
    )


def list_pending() -> list[dict]:
    return (
        client.table("requests")
        .select("*")
        .in_("status", ("pending", "paid"))
        .order("created_at")
        .execute()
        .data
    )


def list_expired_candidates(hours: int = 12) -> list[dict]:
    """Requests still pending that are older than `hours` (expiry sweep)."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    return (
        client.table("requests")
        .select("*")
        .eq("status", "pending")
        .lt("created_at", cutoff)
        .execute()
        .data
    )


def list_requests_since(since: datetime) -> list[dict]:
    return (
        client.table("requests")
        .select("*")
        .gte("created_at", since.isoformat())
        .execute()
        .data
    )


# ---------- services ----------


def list_active_services() -> list[dict]:
    if _fresh(_SVC_CACHE, _SVC_TTL):
        return _SVC_CACHE["v"]
    rows = (
        client.table("services")
        .select("*")
        .eq("active", True)
        .order("sort_order")
        .execute()
        .data
    )
    _SVC_CACHE.update(t=monotonic(), v=rows)
    return rows


def get_service(service_id: str) -> dict | None:
    rows = client.table("services").select("*").eq("id", service_id).execute().data
    return rows[0] if rows else None


def upsert_service(service: dict[str, Any]) -> dict:
    """Insert or replace a service by id (used by /set_service)."""
    client.table("services").upsert(service, on_conflict="id").execute()
    _SVC_CACHE.update(t=0.0, v=None)  # invalidate
    stored = get_service(service["id"])
    assert stored is not None
    return stored
