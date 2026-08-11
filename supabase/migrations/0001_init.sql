-- BunaPay Phase 1 — initial schema
-- users, requests, rate_settings, services (+ seed)

-- ============ users ============
create table if not exists public.users (
  telegram_id      bigint primary key,
  username         text,
  first_name       text,
  is_trusted       boolean   not null default false,
  is_blocked       boolean   not null default false,
  total_requests   integer   not null default 0,
  total_spent_etb  numeric(18,2) not null default 0,
  created_at       timestamptz not null default now()
);

alter table public.users enable row level security;

-- ============ requests ============
create sequence if not exists public.request_id_seq start 1;

create table if not exists public.requests (
  id                        text primary key
                            default ('BUN-' || lpad(nextval('public.request_id_seq')::text, 4, '0')),
  user_id                   bigint not null references public.users(telegram_id) on delete cascade,
  amount_usdt               numeric(18,6) not null,
  amount_etb                numeric(18,2) not null,
  wallet_address            text not null,
  status                    text not null default 'pending'
                            check (status in ('pending','paid','completed','cancelled','rejected','expired')),
  payment_screenshot_file_id text,
  tx_hash                   text,
  admin_notes               text,
  created_at                timestamptz not null default now(),
  paid_at                   timestamptz,
  completed_at              timestamptz
);

create index if not exists requests_user_id_idx    on public.requests (user_id);
create index if not exists requests_status_idx     on public.requests (status);
create index if not exists requests_created_at_idx on public.requests (created_at);

alter table public.requests enable row level security;

-- ============ rate_settings ============
create table if not exists public.rate_settings (
  id          bigint generated always as identity primary key,
  usdt_to_etb numeric(18,2) not null,
  updated_at  timestamptz not null default now(),
  updated_by  bigint
);

alter table public.rate_settings enable row level security;

-- ============ services ============
create table if not exists public.services (
  id          text primary key,
  name        text not null,
  icon_url    text,
  usdt_price  numeric(18,2) not null,
  etb_price   numeric(18,2),
  active      boolean not null default true,
  sort_order  integer not null default 0,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

alter table public.services enable row level security;

-- ============ seed ============
insert into public.rate_settings (usdt_to_etb, updated_by)
values (110, 8731548863)
on conflict do nothing;

insert into public.services (id, name, icon_url, usdt_price, etb_price, sort_order) values
  ('suno',     'Suno AI',          'https://www.google.com/s2/favicons?domain=suno.com&sz=64',        10, 1100, 1),
  ('claude',   'Claude',           'https://www.google.com/s2/favicons?domain=claude.ai&sz=64',       20, 2200, 2),
  ('chatgpt',  'ChatGPT',          'https://www.google.com/s2/favicons?domain=chatgpt.com&sz=64',     20, 2200, 3),
  ('deepseek', 'DeepSeek',         'https://www.google.com/s2/favicons?domain=deepseek.com&sz=64',    10, 1100, 4),
  ('cursor',   'Cursor',           'https://www.google.com/s2/favicons?domain=cursor.com&sz=64',      20, 2200, 5),
  ('telegram', 'Telegram Premium', 'https://www.google.com/s2/favicons?domain=telegram.org&sz=64',     5,  550, 6),
  ('kling',    'Kling AI',         'https://www.google.com/s2/favicons?domain=klingai.com&sz=64',     15, 1650, 7)
on conflict (id) do nothing;
