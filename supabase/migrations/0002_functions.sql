-- BunaPay Phase 1 — database functions

-- Atomic per-user stats increment on completed trade
create or replace function public.bump_user_stats(p_telegram_id bigint, p_etb numeric)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.users
     set total_requests = total_requests + 1,
         total_spent_etb = total_spent_etb + p_etb
   where telegram_id = p_telegram_id;
end;
$$;
