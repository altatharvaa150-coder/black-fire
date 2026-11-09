-- Run against a development Supabase project. All fixture data is rolled back.
begin;
insert into auth.users (id) values
  ('c474fbe1-a461-4ba9-b1b9-864a9c4086ef'), ('cd8698d3-71e4-4be8-bc0a-a0d5618cb611');
set local role authenticated;
select set_config('request.jwt.claims', '{"sub":"c474fbe1-a461-4ba9-b1b9-864a9c4086ef","role":"authenticated"}', true);
insert into public.blackfire_runs (id, owner_id, idempotency_key, payload)
values ('990f325b-8ec7-480e-93e5-110448609ff1', 'c474fbe1-a461-4ba9-b1b9-864a9c4086ef', '29624ba6-8152-486e-aa17-411d07c8312f',
  '{"id":"990f325b-8ec7-480e-93e5-110448609ff1","owner_id":"c474fbe1-a461-4ba9-b1b9-864a9c4086ef","idempotency_key":"29624ba6-8152-486e-aa17-411d07c8312f","request_hash":"test","created_at":"2026-11-09T00:00:00Z","status":"accepted","input":{"prompt":"Synthetic RLS test"}}');
do $$ begin
  if (select count(*) from public.blackfire_runs) <> 1 then raise exception 'Owner cannot read own run'; end if;
end $$;
select set_config('request.jwt.claims', '{"sub":"cd8698d3-71e4-4be8-bc0a-a0d5618cb611","role":"authenticated"}', true);
do $$ begin
  if (select count(*) from public.blackfire_runs) <> 0 then raise exception 'Cross-owner read leak'; end if;
end $$;
update public.blackfire_runs set payload = payload || '{"status":"failed"}' where id='990f325b-8ec7-480e-93e5-110448609ff1';
delete from public.blackfire_runs where id='990f325b-8ec7-480e-93e5-110448609ff1';
select set_config('request.jwt.claims', '{"sub":"c474fbe1-a461-4ba9-b1b9-864a9c4086ef","role":"authenticated"}', true);
do $$ begin
  if (select payload->>'status' from public.blackfire_runs limit 1) is distinct from 'accepted'
    then raise exception 'Cross-owner mutation allowed'; end if;
  begin
    update public.blackfire_runs set owner_id='cd8698d3-71e4-4be8-bc0a-a0d5618cb611',
      payload=jsonb_set(payload,'{owner_id}','"cd8698d3-71e4-4be8-bc0a-a0d5618cb611"');
    raise exception 'Owner reassignment allowed';
  exception when insufficient_privilege then null;
  end;
end $$;
set local role anon;
do $$ begin
  if (select count(*) from public.blackfire_runs) <> 0 then raise exception 'Anonymous read leak'; end if;
end $$;
rollback;
select 'PASS: RLS checks; fixtures rolled back' as result;
