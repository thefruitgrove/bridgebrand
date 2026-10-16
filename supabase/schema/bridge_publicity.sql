-- Public article payloads only. No scoring coefficients or raw evidence here.
create schema if not exists bridge_publicity_private;
revoke all on schema bridge_publicity_private from public, anon, authenticated;
grant usage on schema bridge_publicity_private to service_role;
create table if not exists bridge_publicity_private.snapshots (
  snapshot_hash text primary key check(length(snapshot_hash)=64),
  payload jsonb not null,
  created_at timestamptz not null default now()
);
alter table bridge_publicity_private.snapshots enable row level security;
revoke all on bridge_publicity_private.snapshots from public, anon, authenticated;
grant all on bridge_publicity_private.snapshots to service_role;

create table if not exists public.bridge_publicity_articles (
  id text primary key,
  issue_week text not null,
  slot text not null check(slot in ('WED','FRI','OVERALL')),
  domain text not null check(domain in ('CPR','GOV','UNI','ENT','ALL')),
  scheduled_at timestamptz not null,
  is_example boolean not null default false,
  payload jsonb not null check(jsonb_typeof(payload)='object'),
  snapshot_hash text not null references bridge_publicity_private.snapshots(snapshot_hash),
  status text not null default 'ready' check(status in ('ready','withdrawn')),
  prepared_at timestamptz not null default now(),
  unique(issue_week,slot,domain,is_example)
);
alter table public.bridge_publicity_articles enable row level security;
revoke all on public.bridge_publicity_articles from public,anon,authenticated;
grant select (id,issue_week,slot,domain,scheduled_at,is_example,payload,status,prepared_at)
on public.bridge_publicity_articles to anon,authenticated;
grant all on public.bridge_publicity_articles to service_role;
create policy publicity_release_clock on public.bridge_publicity_articles
for select to anon, authenticated using(status='ready' and scheduled_at <= (select now()));
create index if not exists bridge_publicity_release_idx on public.bridge_publicity_articles(scheduled_at desc) where status='ready';

create or replace function public.bridge_stage_publicity(p_articles jsonb,p_snapshot jsonb)
returns jsonb language plpgsql security invoker set search_path=pg_catalog as $$
declare a jsonb; result_ids jsonb:='[]'::jsonb; sh text; domains integer;
begin
  if jsonb_typeof(p_articles)<>'array' or jsonb_array_length(p_articles) not in (1,4) then raise exception 'Expected one sample/overall or four domain articles'; end if;
  if jsonb_array_length(p_articles)=4 then
    select count(distinct value->>'domain') into domains from jsonb_array_elements(p_articles);
    if domains<>4 or exists(select 1 from jsonb_array_elements(p_articles) where value->>'domain' not in ('CPR','GOV','UNI','ENT')) then raise exception 'Domain batch incomplete';end if;
  end if;
  sh:=p_articles->0->>'snapshot_hash';
  if sh is null or length(sh)<>64 then raise exception 'Frozen snapshot hash required';end if;
  if exists(select 1 from jsonb_array_elements(p_articles) where value->>'snapshot_hash'<>sh or value->>'issue_week'<>(p_articles->0->>'issue_week') or value->>'slot'<>(p_articles->0->>'slot') or value->>'scheduled_at'<>(p_articles->0->>'scheduled_at')) then raise exception 'Mixed batch';end if;
  insert into bridge_publicity_private.snapshots(snapshot_hash,payload) values(sh,p_snapshot) on conflict do nothing;
  for a in select value from jsonb_array_elements(p_articles) loop
    if a->'payload'->>'title' is null or jsonb_array_length(a->'payload'->'sections')<3 or a->'payload'->>'template_version' is null then raise exception 'Article validation missing';end if;
    insert into public.bridge_publicity_articles(id,issue_week,slot,domain,scheduled_at,is_example,payload,snapshot_hash)
    values(a->>'id',a->>'issue_week',a->>'slot',a->>'domain',(a->>'scheduled_at')::timestamptz,coalesce((a->>'is_example')::boolean,false),a->'payload',sh)
    on conflict(id) do update set payload=excluded.payload,snapshot_hash=excluded.snapshot_hash,prepared_at=now()
      where public.bridge_publicity_articles.scheduled_at>now();
    result_ids:=result_ids||jsonb_build_array(a->>'id');
  end loop;
  return jsonb_build_object('article_ids',result_ids,'snapshot_hash',sh);
end $$;
revoke all on function public.bridge_stage_publicity(jsonb,jsonb) from public,anon,authenticated;
grant execute on function public.bridge_stage_publicity(jsonb,jsonb) to service_role;
notify pgrst,'reload schema';
