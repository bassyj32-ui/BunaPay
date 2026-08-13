# BunaPay — Master Build Plan (v3)

Telegram Bot · Single Supplier · Manual USDT Release (BSC/BEP20)

Tick `☐` → `☑` as each task completes. Keep this file updated — it is the source of truth for what is done, what is left, and what comes next.

---

## Phase Map

| Phase | Name | Status |
|---|---|---|
| 0 | Design & Mockup | ☑ DONE |
| 1 | Telegram Bot MVP | ☐ IN PROGRESS (this build) |
| 2 | Trusted Suppliers + Commission | ☐ PLANNED |
| 3 | Full Web Platform | ☐ PLANNED |
| 4 | Expansion (mobile app, more coins) | ☐ PLANNED |

---

## Phase 0 — Design & Mockup (DONE)

- ☑ Apple Wallet-inspired design approved: light cream base, gold `#C9A84C` brand accents
- ☑ Interactive mockup built & approved — `bot-mockup.html`
- ☑ All emoji removed from UI — pure typography + real brand logos (Google favicons)
- ☑ Compact rate card: logo row + `CURRENT RATE` + `1 USDT = 110 ETB`
- ☑ Bold pay-path card: `TELEBIRR → BSC BEP20 → WE CONFIRM` (final step gold)
- ☑ iOS Settings-style quote rows (muted label left, tabular value right, Total emphasized)
- ☑ Services as static 2-column grid + `More ›` paging — no animations (Telegram can't render them)
- ☑ Network confirmed: **BSC/BEP20**, wallets `0x` + 40 hex chars
- ☑ Rate: 1 USDT = 110 ETB (persisted in DB, admin-changeable at runtime)

---

## Telegram Rendering Reality (mockup → bot translation)

Telegram bot messages support **HTML formatting only**: bold, italic, underline, strikethrough, code, links. There is **no** text color, background, border, rounded card, CSS animation, horizontal scroll, or styling on keyboard buttons — every inline button looks identical.

So the Apple look in the real bot is achieved with **typography + spacing + structure**:

| Mockup (CSS) | Real bot (HTML) |
|---|---|
| Rounded cards | Sections separated by blank lines + `──` rules |
| Colored status pills | Bold CAPS labels: `PENDING` / `PAID` / `COMPLETED` |
| Styled primary buttons | Buttons look the same; hierarchy via text & order |
| Services marquee / grid | Paged carousel: 2 columns per page + `More ›` |
| Blur / gradients | Not possible — use clean spacing instead |

The mockup stays as the vision; the bot is its honest Telegram rendering.

---

## Phase 1 — Locked Decisions

| Topic | Decision |
|---|---|
| Database | **Supabase (Postgres)** — project `cihjlpxkmpydnftdtbvw` (BunaPay, eu-west-1). Service role key server-side only |
| USDT network | **BSC (BEP20)** — 0x wallets (42 chars). Cheapest Binance withdrawal for manual sends |
| Admin workflow | **Inline action buttons** on notifications (Confirm / Complete / Reject). Text commands kept as backup |
| Build approach | Fresh build in `d:\trae\BunaPay` — no clone |
| Extra features | Status notifications · cancel + 12h auto-expiry · min/max + abuse guards · daily stats to admin |
| Daily scheduled msg | **Stats summary** (Supabase handles backups) |
| Coding rules | `AGENTS.md` at repo root — mandatory (never view images, evidence-based verification) |
| Repo | `bassyj32-ui/BunaPay` (GitHub, empty) — init + push from local |
| Monitoring | **Sentry** — project `bunapay`, org `scholarnova` (us.sentry.io). DSN in `.env` only |
| Design | Apple Wallet style per Phase 0; no emoji in bot copy |
| Services | Live in Supabase `services` table; admin-managed via `/set_service` |

---

## Phase 1 — Telegram Bot MVP

### Architecture

```
Telegram Users ──► Telegram Bot API ──► BunaPay Bot (Python 3.11)
                                          │  handlers / Conversation / JobQueue
                                          │  (supabase-py, service role key)
                                          ▼
                                    Supabase Postgres
                                    (users, requests, rate_settings, services)
```

- Polling mode (`run_polling`) — no webhook in Phase 1.
- `python-telegram-bot` JobQueue: 12h expiry sweep + daily stats.

### File Structure

```
d:\trae\BunaPay\
├── AGENTS.md            # AI coding rules (mandatory)
├── bot.py               # Main bot: handlers, conversation, callbacks
├── config.py            # Env loader (.env)
├── db.py                # Supabase client + query helpers
├── messages.py          # Apple-style message composer (HTML sections)
├── schema.sql           # Supabase migration (4 tables + seed)
├── requirements.txt
├── .env                 # Secrets — NEVER commit
├── .env.template        # Committed template
├── BUILD_PLAN.md        # This file
├── PRD.md               # Product spec
├── bot-mockup.html      # Approved design vision
└── pics/                # brand assets (optimized in 1.5)
```

### 1.0 Foundation

- ☑ Init git repo, `.gitignore` (excludes `.env`, `pics/` originals if needed), commit scaffold
- ☑ Create `.env.template` with all keys (section 1.6) — commit it
- ☑ `requirements.txt`: `python-telegram-bot`, `supabase`, `python-dotenv`, `sentry-sdk`
- ☑ `config.py` — loads env, fails fast on missing required keys (verified: raises `ConfigError` on missing vars)
- ☑ Push scaffold to `bassyj32-ui/BunaPay` (main @ 72133eb)

### 1.1 Database (`schema.sql`)

**users**
| column | type | notes |
|---|---|---|
| telegram_id | BIGINT PK | Telegram numeric ID |
| username | TEXT | nullable |
| first_name | TEXT | |
| is_trusted | BOOLEAN | default false |
| is_blocked | BOOLEAN | default false |
| total_requests | INTEGER | default 0 |
| total_spent_etb | NUMERIC | default 0 |
| created_at | TIMESTAMPTZ | default now() |

**requests**
| column | type | notes |
|---|---|---|
| id | TEXT PK | e.g. `BUN-0001` (from Postgres sequence) |
| user_id | BIGINT FK → users.telegram_id | |
| amount_usdt | NUMERIC | |
| amount_etb | NUMERIC | |
| wallet_address | TEXT | BSC, validated `^0x[0-9a-fA-F]{40}$` |
| status | TEXT | pending · paid · completed · cancelled · rejected · expired |
| payment_screenshot_file_id | TEXT | Telegram file_id (survives restarts) |
| tx_hash | TEXT | set on completion |
| admin_notes | TEXT | |
| created_at | TIMESTAMPTZ | |
| paid_at | TIMESTAMPTZ | |
| completed_at | TIMESTAMPTZ | |

**rate_settings**
| column | type | notes |
|---|---|---|
| id | SERIAL PK | |
| usdt_to_etb | NUMERIC | persists until admin changes it |
| updated_at | TIMESTAMPTZ | |
| updated_by | BIGINT | admin telegram_id |

**services** (NEW — powers the subscriptions browser)
| column | type | notes |
|---|---|---|
| id | TEXT PK | slug e.g. `suno` |
| name | TEXT | display name e.g. `Suno AI` |
| icon_url | TEXT | brand icon (Google favicon) |
| usdt_price | NUMERIC | e.g. 10 |
| etb_price | NUMERIC | stored at seed time (rate can change later) |
| active | BOOLEAN | default true |
| sort_order | INTEGER | default 0 |
| created_at / updated_at | TIMESTAMPTZ | |

Seed the 7 services:
`Suno AI 10 · Claude 20 · ChatGPT 20 · DeepSeek 10 · Cursor 20 · Telegram Premium 5 · Kling AI 15` (USDT).

Tasks:
- ☑ Write `schema.sql` (4 tables + sequences + seed) — `supabase/migrations/0001_init.sql` + `0002_functions.sql` (atomic stats RPC)
- ☑ Apply to Supabase via MCP; verify tables exist (verified: users, requests, rate_settings, services + FK + status check + RLS)
- ☑ `db.py` — supabase client + helpers (users, rate, requests, services). Smoke-tested live: rate=110, 7 services, create/update/cleanup OK

### 1.2 User Flows (in `bot.py`)

- ☑ `/start` → **hero screen straight to work** (no menu): rate card + pay-path line + amount tiles + services browser. HTML version of the approved mockup first screen (verified live)
- ☑ Amount tiles: `10 / 20 / 50 / 100 USDT` (2 per row) + `Other amount` (tiles verified live)
- ☑ Custom amount: min 5 / max 100 USDT enforced (verified live: 3 rejected, 50 accepted → 9,500 ETB)
- ☑ Quote message: iOS-style rows (USDT / Rate / Total emphasized) (verified live)
- ☑ Ask BSC wallet → validate `0x` + 40 hex (verified live)
- ☑ Telebirr payment details (name/number from env) → wait for photo upload (verified live)
- ☑ Screenshot stored as file_id → create request (status `pending`, id `BUN-####`) (verified live: BUN-0005)
- ☑ **Services browser**: paged carousel, 2 columns/page + `More ›` / `‹ Back`; tapping a service shows its price + `Get N USDT` (verified live: Suno 10 USDT → 1,900 ETB quote)
- ☐ My Requests (history with status labels) (coded — verify in 1.7)
- ☐ How it works + terms line (coded — verify in 1.7)
- ☑ Blocked users rejected at `/start` (coded); max **2 pending** per user (guard verified live)

### 1.3 Admin Flows (restricted to `TELEGRAM_ADMIN_ID`)

- ☑ New-request notification: details + screenshot + inline buttons `Confirm Payment` / `Complete` / `Reject` (verified live: photo + text card with buttons)
- ☑ Confirm → `paid`, user notified (DB update proven live; user notify coded)
- ☑ Complete → prompts TX hash (validate `0x` + 16+ hex) → `completed`, user notified (verified live: BUN-0005 completed + thanks message)
- ☑ Reject → `rejected`, user notified (verified live: BUN-0007, BUN-0008 → rejected + notification)
- ☑ `/dashboard` — all pending requests, one card per request WITH action buttons (verified live; enhanced so admin can act on already-notified orders — was a gap: buttons only existed on fresh notifications and were consumed after press)
- ☑ `/set_rate 110` — updates rate for future requests (code-verified: inserts rate_settings row, invalidates cache)
- ☑ `/set_service` — add / update / deactivate a service (name, icon, USDT price) (code-verified)
- ☑ `/trusted_list` `/add_trusted @u` `/remove_trusted @u` `/block_user @u` `/unblock_user @u` (code-verified, admin-guarded)

### 1.4 Automation & Guards (JobQueue)

- ☑ 12h expiry sweep (every 10 min): pending > 12h → `expired`, notify user + admin (job scheduled + ran clean; expiry action verify in 1.7)
- ☐ Daily stats (23:45 Africa/Addis_Ababa): new/pending/completed counts, ETB volume, completion rate → admin chat (scheduled — first fire 23:45)
- ☐ Rate guard: no rate set → bot tells user "unavailable", reminds admin via `/set_rate` (coded — verify in 1.7)

### 1.5 Assets & Polish

- ☑ Optimize `pics/bunapay_logo.png` (~1.5MB) and `pics/bunapay_hero.png` (~1.9MB) → web copies < 400KB each (via script; never by viewing images) — verified: logo 355KB, hero 372KB (`compress_assets.py`)
- ☑ `messages.py` composer: consistent section builders (rate card, quote rows, status label, pay path) so every screen matches the approved design language — built in 1.2, verified live

### 1.6 Environment Variables (`.env`)

```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_ADMIN_ID=...
SUPABASE_URL=https://<ref>.supabase.co
SUPABASE_SERVICE_KEY=...
TELEBIRR_NAME=BunaPay Services
TELEBIRR_NUMBER=09XX XXX XXX
SENTRY_DSN=https://...@o4511656889614336.ingest.us.sentry.io/4511893022900224
```

- `SENTRY_DSN` optional — unset → bot runs without Sentry.
- Sentry init at top of `bot.py`; scope set with user telegram_id + request id; Telegram update context attached as extra data.
- Verified live: DSN/ingest/project proven via manual envelope POST (HTTP 200) → event `2a334f0d...` searchable in `scholarnova` → BunaPay; bot errors land with stack traces (BUNAPAY-2..5); error handler sets user scope (telegram id + username).

### 1.7 Testing Checklist (verify with getUpdates / Supabase queries / bot logs — never images, per AGENTS.md)

- ☑ `/start` shows hero screen (rate card + tiles + services) with no emoji — confirmed live, zero errors in bot log
- ☑ Amount flow: preset + custom, min/max enforced, ETB total correct at current rate — verified live in DB: custom 50×190=9,500 ETB; service 10×190=1,900 (BUN-0005/6/7)
- ☑ No-rate guard works — code-verified (rate currently 190; guard at /start + amount paths)
- ☑ Wallet validation rejects bad BSC addresses — rejected live; valid 42-char stored in all 3 requests
- ☑ Screenshot accepted; file_id stored in Supabase `requests` — file_id present in BUN-0005/6/7
- ☑ Services carousel pages correctly; service price → quote → same flow — confirmed live (Suno 10 USDT → 1,900 ETB)
- ☑ Admin notification with buttons; Confirm / Complete(+TX) / Reject update DB + notify user — verified live: BUN-0006 paid+paid_at, BUN-0005 completed+tx_hash+completed_at, BUN-0007 rejected; log PATCH/editMessageText 200
- ☑ `/cancel` works — verified live (aborts in-progress flow; DB rows only exist post-screenshot, so nothing to cancel there — abandoned rows covered by 12h expiry)
- ☐ 12h expiry fires (test with shortened window locally) — code-reviewed: sweep marks expired + notifies; next scheduled run ≤12h
- ☑ Max-2-pending guard — code-verified (checked at /start + amount path via count_pending_for_user ≥ 2)
- ☑ Blocked user rejected — code-verified (is_blocked check at /start)
- ☑ `/dashboard` `/set_rate` `/set_service` trust/block commands admin-only — code-verified (all guarded by `_is_admin`); `/dashboard` live-verified, others code-verified
- ☑ Complete is 2-step (button → TX hash prompt → hash → completed) — confirmed in live log; BUN-0005 completed with tx_hash
- ☐ Daily stats message sends — code-reviewed; scheduled 23:45 Africa/Addis_Ababa
- ☑ Sentry: forced test error appears in `scholarnova` → BunaPay project with Telegram context — proven: envelope POST 200 + event searchable; bot errors BUNAPAY-2..5 landed
- ☑ Secrets never in code/commits — `git grep` for token/DSN/service-key → 0 matches

### 1.8 Deploy (Railway)

- ☑ Push to `bassyj32-ui/BunaPay` (main; incl. `railway.json` → Nixpacks, start `python bot.py`, restart on failure)
- ☑ Railway project from GitHub repo, env vars per 1.6 (first deploy crashed `ConfigError: Missing required env var: TELEGRAM_BOT_TOKEN` → all 7 vars set as separate entries → Live)
- ☑ Deploy; local bot killed (0 processes) so no getUpdates 409 conflict; monitoring = Railway auto-restart (`ON_FAILURE`) + Sentry alerts — UptimeRobot N/A (polling bot has no HTTP endpoint)
- ☑ Supabase hosts DB (persistent across redeploys)

### 1.9 Telegram Mini App (order form)

- ☑ `webapp/` static site (index.html + app.js + app.css + railway.json): service grid, amount presets/custom, BSC wallet, submit via `Telegram.WebApp.sendData`
- ☑ Bot: `MINI_APP_URL` (optional env) + "Open BunaPay App" WebApp button on hero; payload embeds current rate + active services
- ☑ Bot: `webapp_order_received` validates rate / min-max / wallet / pending-guard / service, then prompts for screenshot; `mini_screenshot_received` reuses create+notify path
- ☑ Deploy: single Railway service hosts bot + webapp (`start_static_server` serves `webapp/` on `PORT`, default 3000); `MINI_APP_URL` = bot service domain

---

## Phase 2 — Trusted Suppliers + Commission (PLANNED — details on start)

Goal: scale supply without losing trust. Whitelisted suppliers, pre-funded escrow, admin commission.

- ☐ Supplier whitelist + `/post_offer` `/my_offers` (whitelisted only)
- ☐ Escrow: suppliers pre-fund USDT to your wallet before posting offers
- ☐ Commission 0.5–1.5% auto-calculated per trade
- ☐ Admin: `/approve_supplier` `/remove_supplier` `/set_commission` `/supplier_dashboard`
- ☐ Success: 200 daily users, 5+ active suppliers, <0.5% disputes

## Phase 3 — Full Web Platform (PLANNED)

Goal: the "Binance of Ethiopia" — web + bot on the same Postgres.

- ☐ FastAPI backend (SQLAlchemy) on the Supabase Postgres
- ☐ React + Vite frontend (mobile-responsive), the mockup's marquee lives here
- ☐ Secure escrow release, trade timeout 90 min, audit logging
- ☐ Multi-trader + reputation + dispute workflow
- ☐ Admin panel; deploy frontend (Vercel) + backend (Render/Railway)
- ☐ Success: 1,000 daily users, 50+ verified traders

## Phase 4 — Expansion (PLANNED)

- ☐ Mobile app (React Native / Flutter) with push notifications
- ☐ More assets: BTC, ETH
- ☐ ETB stablecoin integration
- ☐ Regional expansion

---

## How to work this plan

1. When a task is finished, change its `☐` to `☑` and commit with the file.
2. Don't skip to Phase 2 until Phase 1 checklist (1.7) is fully `☑`.
3. Every claim (test passed, row written, notification sent) must be backed by structured evidence per `AGENTS.md`.
