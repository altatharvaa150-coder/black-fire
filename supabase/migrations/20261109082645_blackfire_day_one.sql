-- Day-one client-owned task records. Not a trusted billing or inference audit ledger.
create table public.blackfire_runs (
  id uuid primary key,
  owner_id uuid not null references auth.users(id) on delete cascade,
  idempotency_key uuid not null,
  created_at timestamptz not null default now(),
  payload jsonb not null,
  constraint blackfire_runs_owner_request unique (owner_id, idempotency_key),
  constraint blackfire_runs_payload_shape check (
    jsonb_typeof(payload) = 'object'
    and payload ?& array['id','owner_id','idempotency_key','request_hash','created_at','status','input']
    and payload->>'id' = id::text
    and payload->>'owner_id' = owner_id::text
    and payload->>'idempotency_key' = idempotency_key::text
    and payload->>'status' in ('accepted','completed','paused','failed')
    and octet_length(payload::text) <= 100000
  )
);
create index blackfire_runs_owner_created on public.blackfire_runs(owner_id, created_at desc);
alter table public.blackfire_runs enable row level security;
revoke all on public.blackfire_runs from anon, authenticated;
-- anon can issue a readiness SELECT, but has no policy and therefore sees no rows.
grant select on public.blackfire_runs to anon;
grant select, insert, update, delete on public.blackfire_runs to authenticated;
create policy blackfire_runs_select on public.blackfire_runs for select to authenticated
  using ((select auth.uid()) = owner_id);
create policy blackfire_runs_insert on public.blackfire_runs for insert to authenticated
  with check ((select auth.uid()) = owner_id);
create policy blackfire_runs_update on public.blackfire_runs for update to authenticated
  using ((select auth.uid()) = owner_id) with check ((select auth.uid()) = owner_id);
create policy blackfire_runs_delete on public.blackfire_runs for delete to authenticated
  using ((select auth.uid()) = owner_id);
comment on table public.blackfire_runs is
  'Black Fire day-one mock records. Owner editable; never use for trusted quotas or billing.';
