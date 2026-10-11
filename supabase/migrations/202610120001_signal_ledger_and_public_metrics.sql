begin;

create table if not exists public.bridge_event_ledger (
  id uuid primary key default gen_random_uuid(),
  entity_id uuid not null references public.bridge_entities(id) on delete cascade,
  raw_item_id uuid references public.bridge_raw_items(id) on delete set null,
  event_key text not null,
  domain text not null check (domain in ('CPR','STAR','GOV','UNI')),
  event_type text not null check (event_type in ('issue','response','activity','outcome')),
  lifecycle_status text not null check (lifecycle_status in ('detected','observed','recovery_candidate','verified','resolved','recurred')),
  direction smallint not null check (direction between -1 and 1),
  severity smallint not null default 1 check (severity between 1 and 5),
  action_strength numeric(6,2) not null default 0 check (action_strength between 0 and 100),
  response_quality numeric(6,2) not null default 0 check (response_quality between 0 and 100),
  axes text[] not null default '{}',
  source_ids text[] not null default '{}',
  evidence_count integer not null default 1 check (evidence_count >= 1),
  confidence numeric(5,4) not null default 0 check (confidence between 0 and 1),
  review_status text not null default 'pending' check (review_status in ('auto','pending','approved','rejected')),
  occurred_at timestamptz not null,
  last_seen_at timestamptz not null,
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(entity_id, event_key)
);

create index if not exists bridge_event_ledger_entity_time_idx
  on public.bridge_event_ledger(entity_id, occurred_at desc);
create index if not exists bridge_event_ledger_raw_item_idx
  on public.bridge_event_ledger(raw_item_id);
create index if not exists bridge_event_ledger_review_idx
  on public.bridge_event_ledger(review_status, event_type, occurred_at desc);

alter table public.bridge_event_ledger enable row level security;
revoke all on table public.bridge_event_ledger from anon, authenticated;
create policy "deny direct public event access" on public.bridge_event_ledger
  for all to anon, authenticated using (false) with check (false);
grant select, insert, update, delete on public.bridge_event_ledger to service_role;

alter table public.bridge_index_metrics
  add column if not exists four_week_average numeric(6,2) check (four_week_average between 0 and 100),
  add column if not exists cumulative_activity numeric(14,2) not null default 0,
  add column if not exists observed_weeks integer not null default 0;
create index if not exists bridge_index_metrics_methodology_idx
  on public.bridge_index_metrics(methodology_version);

create or replace view public.bridge_public_latest_rankings
with (security_invoker = true) as
select r.as_of_date, r.domain, r.ranking_type, r.rank, r.previous_rank,
       r.rank_change, r.score, r.score_change, r.trust_grade,
       e.external_id, e.name, e.category, e.subcategory,
       m.daily_index, m.weekly_index, m.last_week_index, m.wow_delta,
       m.weighted_index, m.activity_points, m.cumulative_performance,
       m.momentum, m.stability, m.observed_days,
       m.four_week_average, m.cumulative_activity, m.observed_weeks
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

grant select on public.bridge_public_latest_rankings to anon, authenticated, service_role;

commit;
