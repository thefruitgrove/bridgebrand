begin;

insert into public.bridge_source_registry(id, name, family, base_url, terms_url, collection_mode, default_refresh)
values ('google_news_discovery', 'Google News Discovery', 'major_news', 'https://news.google.com',
        'https://policies.google.com/terms', 'rss', interval '1 day')
on conflict (id) do update set enabled = true, default_refresh = excluded.default_refresh;

alter table public.bridge_entities
  add column if not exists lifecycle_status text not null default 'monitored'
    check (lifecycle_status in ('candidate','monitored','eligible','published','retired')),
  add column if not exists discovered_at timestamptz,
  add column if not exists last_observed_at timestamptz;

create table if not exists public.bridge_entity_candidates (
  id uuid primary key default gen_random_uuid(),
  domain text not null check (domain in ('CPR','STAR','GOV','UNI')),
  canonical_name text not null,
  aliases text[] not null default '{}',
  discovery_score numeric(7,2) not null default 0,
  mention_count integer not null default 0,
  publisher_count integer not null default 0,
  status text not null default 'discovered'
    check (status in ('discovered','review','promoted','rejected')),
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  evidence jsonb not null default '[]',
  metadata jsonb not null default '{}',
  unique(domain, canonical_name)
);

create index if not exists bridge_entity_candidates_priority_idx
  on public.bridge_entity_candidates(status, discovery_score desc, last_seen_at desc);

create table if not exists public.bridge_index_metrics (
  id uuid primary key default gen_random_uuid(),
  entity_id uuid not null references public.bridge_entities(id),
  as_of_date date not null,
  daily_index numeric(6,2) check (daily_index between 0 and 100),
  weekly_index numeric(6,2) check (weekly_index between 0 and 100),
  last_week_index numeric(6,2) check (last_week_index between 0 and 100),
  wow_delta numeric(7,2),
  weighted_index numeric(6,2) check (weighted_index between 0 and 100),
  activity_points numeric(12,2) not null default 0,
  cumulative_performance numeric(6,2) check (cumulative_performance between 0 and 100),
  momentum numeric(7,2),
  stability numeric(6,2) check (stability between 0 and 100),
  observed_days integer not null default 0,
  methodology_version text not null references public.bridge_methodology_versions(version),
  diagnostics jsonb not null default '{}',
  created_at timestamptz not null default now(),
  unique(entity_id, as_of_date, methodology_version)
);

create index if not exists bridge_index_metrics_date_entity_idx
  on public.bridge_index_metrics(as_of_date desc, entity_id);

create or replace view public.bridge_public_latest_rankings
with (security_invoker = true) as
select r.as_of_date, r.domain, r.ranking_type, r.rank, r.previous_rank,
       r.rank_change, r.score, r.score_change, r.trust_grade,
       e.external_id, e.name, e.category, e.subcategory,
       m.daily_index, m.weekly_index, m.last_week_index, m.wow_delta,
       m.weighted_index, m.activity_points, m.cumulative_performance,
       m.momentum, m.stability, m.observed_days
from public.bridge_rankings r
join public.bridge_entities e on e.id = r.entity_id
left join public.bridge_index_metrics m
  on m.entity_id = r.entity_id
 and m.as_of_date = r.as_of_date
 and m.methodology_version = r.methodology_version
where r.published_at is not null
  and r.as_of_date = (
    select max(r2.as_of_date) from public.bridge_rankings r2
    where r2.domain = r.domain and r2.ranking_type = r.ranking_type
      and r2.published_at is not null
  );

alter table public.bridge_entity_candidates enable row level security;
alter table public.bridge_index_metrics enable row level security;
revoke all on table public.bridge_entity_candidates, public.bridge_index_metrics from anon, authenticated;
create policy "deny public candidate access" on public.bridge_entity_candidates
  for all to anon, authenticated using (false) with check (false);
create policy "public read published metric rows" on public.bridge_index_metrics
  for select to anon, authenticated using (
    exists (
      select 1 from public.bridge_rankings r
      where r.entity_id = bridge_index_metrics.entity_id
        and r.as_of_date = bridge_index_metrics.as_of_date
        and r.methodology_version = bridge_index_metrics.methodology_version
        and r.published_at is not null
    )
  );
grant select on public.bridge_index_metrics to anon, authenticated;
grant select, insert, update, delete on public.bridge_entity_candidates, public.bridge_index_metrics to service_role;

commit;
