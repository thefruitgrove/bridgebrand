begin;

create extension if not exists pgcrypto;

create table if not exists public.bridge_methodology_versions (
  version text primary key,
  config jsonb not null,
  status text not null default 'shadow' check (status in ('draft','shadow','active','retired')),
  effective_from timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists public.bridge_entities (
  id uuid primary key default gen_random_uuid(),
  domain text not null check (domain in ('CPR','STAR','GOV','UNI')),
  external_id text not null,
  name text not null,
  category text,
  subcategory text,
  aliases text[] not null default '{}',
  metadata jsonb not null default '{}',
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(domain, external_id)
);
create index if not exists bridge_entities_domain_active_idx
  on public.bridge_entities(domain, active);

create table if not exists public.bridge_source_registry (
  id text primary key,
  name text not null,
  family text not null check (family in ('official','regulatory','public_data','major_news','trade_news','community_index')),
  base_url text,
  terms_url text,
  enabled boolean not null default true,
  collection_mode text not null check (collection_mode in ('api','rss','file','manual')),
  default_refresh interval not null default interval '1 day',
  created_at timestamptz not null default now()
);

create table if not exists public.bridge_collection_runs (
  id uuid primary key default gen_random_uuid(),
  source_id text not null references public.bridge_source_registry(id),
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  status text not null default 'running' check (status in ('running','success','partial','failed')),
  window_start timestamptz not null,
  window_end timestamptz not null,
  fetched_count integer not null default 0,
  accepted_count integer not null default 0,
  rejected_count integer not null default 0,
  error_code text,
  error_detail text,
  diagnostics jsonb not null default '{}'
);
create index if not exists bridge_collection_runs_source_started_idx
  on public.bridge_collection_runs(source_id, started_at desc);

create table if not exists public.bridge_raw_items (
  id uuid primary key default gen_random_uuid(),
  source_id text not null references public.bridge_source_registry(id),
  collection_run_id uuid not null references public.bridge_collection_runs(id) on delete cascade,
  source_item_id text,
  canonical_url text,
  title text not null,
  publisher text,
  published_at timestamptz,
  collected_at timestamptz not null default now(),
  payload jsonb not null default '{}',
  content_hash text not null,
  unique(source_id, content_hash)
);
create index if not exists bridge_raw_items_published_idx
  on public.bridge_raw_items(published_at desc);

create table if not exists public.bridge_signals (
  id uuid primary key default gen_random_uuid(),
  entity_id uuid not null references public.bridge_entities(id),
  raw_item_id uuid references public.bridge_raw_items(id),
  source_id text not null references public.bridge_source_registry(id),
  axis char(1) not null check (axis in ('B','R','I','D','G','E')),
  signal_type text not null,
  direction smallint not null check (direction between -1 and 1),
  magnitude numeric(8,4) not null check (magnitude between 0 and 100),
  confidence numeric(5,4) not null check (confidence between 0 and 1),
  occurred_at timestamptz not null,
  expires_at timestamptz,
  review_status text not null default 'auto' check (review_status in ('auto','pending','approved','rejected')),
  rationale text,
  ruleset_version text not null,
  created_at timestamptz not null default now(),
  unique(entity_id, raw_item_id, axis, signal_type)
);
create index if not exists bridge_signals_entity_axis_time_idx
  on public.bridge_signals(entity_id, axis, occurred_at desc);
create index if not exists bridge_signals_pending_idx
  on public.bridge_signals(review_status, created_at)
  where review_status = 'pending';

create table if not exists public.bridge_axis_observations (
  id uuid primary key default gen_random_uuid(),
  entity_id uuid not null references public.bridge_entities(id),
  as_of_date date not null,
  axis char(1) not null check (axis in ('B','R','I','D','G','E')),
  score numeric(5,2) check (score between 0 and 100),
  confidence numeric(5,4) not null check (confidence between 0 and 1),
  coverage numeric(5,4) not null check (coverage between 0 and 1),
  source_families integer not null default 0,
  evidence_count integer not null default 0,
  freshness_days integer,
  status text not null check (status in ('measured','carried','missing','review_required')),
  methodology_version text not null references public.bridge_methodology_versions(version),
  diagnostics jsonb not null default '{}',
  created_at timestamptz not null default now(),
  unique(entity_id, as_of_date, axis, methodology_version)
);

create table if not exists public.bridge_scores (
  id uuid primary key default gen_random_uuid(),
  entity_id uuid not null references public.bridge_entities(id),
  as_of_date date not null,
  score numeric(5,2) check (score between 0 and 100),
  confidence_score numeric(5,2) not null check (confidence_score between 0 and 100),
  trust_grade text not null check (trust_grade in ('A','B','C','D','N/R')),
  axes_used char(1)[] not null default '{}',
  publish_status text not null check (publish_status in ('shadow','eligible','published','withheld')),
  methodology_version text not null references public.bridge_methodology_versions(version),
  diagnostics jsonb not null default '{}',
  created_at timestamptz not null default now(),
  unique(entity_id, as_of_date, methodology_version)
);
create index if not exists bridge_scores_date_entity_idx
  on public.bridge_scores(as_of_date desc, entity_id);

create table if not exists public.bridge_rankings (
  id uuid primary key default gen_random_uuid(),
  as_of_date date not null,
  domain text not null check (domain in ('CPR','STAR','GOV','UNI')),
  ranking_type text not null,
  entity_id uuid not null references public.bridge_entities(id),
  rank integer not null check (rank > 0),
  previous_rank integer,
  rank_change integer,
  score numeric(5,2) not null,
  score_change numeric(6,2),
  trust_grade text not null,
  methodology_version text not null references public.bridge_methodology_versions(version),
  published_at timestamptz,
  unique(as_of_date, domain, ranking_type, entity_id, methodology_version)
);
create index if not exists bridge_rankings_lookup_idx
  on public.bridge_rankings(domain, ranking_type, as_of_date desc, rank);

create table if not exists public.bridge_pipeline_alerts (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references public.bridge_collection_runs(id),
  severity text not null check (severity in ('info','warning','critical')),
  code text not null,
  message text not null,
  context jsonb not null default '{}',
  resolved_at timestamptz,
  created_at timestamptz not null default now()
);

alter table public.bridge_methodology_versions enable row level security;
alter table public.bridge_entities enable row level security;
alter table public.bridge_source_registry enable row level security;
alter table public.bridge_collection_runs enable row level security;
alter table public.bridge_raw_items enable row level security;
alter table public.bridge_signals enable row level security;
alter table public.bridge_axis_observations enable row level security;
alter table public.bridge_scores enable row level security;
alter table public.bridge_rankings enable row level security;
alter table public.bridge_pipeline_alerts enable row level security;

create or replace view public.bridge_public_latest_rankings
with (security_invoker = true) as
select r.as_of_date, r.domain, r.ranking_type, r.rank, r.previous_rank,
       r.rank_change, r.score, r.score_change, r.trust_grade,
       e.external_id, e.name, e.category, e.subcategory
from public.bridge_rankings r
join public.bridge_entities e on e.id = r.entity_id
where r.published_at is not null
  and r.as_of_date = (
    select max(r2.as_of_date) from public.bridge_rankings r2
    where r2.domain = r.domain and r2.ranking_type = r.ranking_type
      and r2.published_at is not null
  );

create policy "public read active entities" on public.bridge_entities
  for select to anon, authenticated using (active = true);
create policy "public read published rankings" on public.bridge_rankings
  for select to anon, authenticated using (published_at is not null);

grant select on public.bridge_public_latest_rankings to anon, authenticated;

insert into public.bridge_source_registry(id, name, family, base_url, terms_url, collection_mode, default_refresh)
values
  ('opendart', 'OpenDART', 'regulatory', 'https://opendart.fss.or.kr', 'https://opendart.fss.or.kr/guide/main.do', 'api', interval '1 day'),
  ('google_news_rss', 'Google News RSS', 'major_news', 'https://news.google.com', 'https://policies.google.com/terms', 'rss', interval '1 day')
on conflict (id) do update set
  name = excluded.name, family = excluded.family, base_url = excluded.base_url,
  terms_url = excluded.terms_url, collection_mode = excluded.collection_mode,
  default_refresh = excluded.default_refresh;

commit;
