-- Internal weekly observability ledger. No anonymous or authenticated access.
create table if not exists public.bridge_axis_weekly_coverage (
  id uuid primary key default gen_random_uuid(),
  entity_id uuid not null references public.bridge_entities(id) on delete cascade,
  week_start date not null,
  week_end date not null,
  as_of_date date not null,
  axis char(1) not null check (axis in ('B','R','I','D','G','E')),
  state text not null check (state in ('O','M','R','F')),
  public_state text not null check (public_state in ('observed','maintained','reference','failed')),
  new_observation_days integer not null default 0 check (new_observation_days >= 0),
  maintained_days integer not null default 0 check (maintained_days >= 0),
  reference_days integer not null default 0 check (reference_days >= 0),
  collection_checked boolean not null default false,
  reference_streak_weeks integer not null default 0 check (reference_streak_weeks >= 0),
  remediation_stage text not null default 'normal_reference',
  methodology_version text not null,
  diagnostics jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(entity_id, week_start, axis, methodology_version)
);

create index if not exists idx_bridge_axis_weekly_coverage_week
  on public.bridge_axis_weekly_coverage(week_start desc, entity_id, axis);
create index if not exists idx_bridge_axis_weekly_coverage_remediation
  on public.bridge_axis_weekly_coverage(remediation_stage, reference_streak_weeks desc)
  where state = 'R';

alter table public.bridge_axis_weekly_coverage enable row level security;
revoke all on public.bridge_axis_weekly_coverage from anon, authenticated;
