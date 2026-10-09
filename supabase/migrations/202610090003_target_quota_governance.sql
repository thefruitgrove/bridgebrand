begin;

-- New Supabase projects no longer expose SQL-created objects to the Data API
-- automatically. Keep internal access explicit and public access minimal.
alter default privileges for role postgres in schema public
  revoke select, insert, update, delete on tables from anon, authenticated;
alter default privileges for role postgres in schema public
  revoke usage, select on sequences from anon, authenticated;
alter default privileges for role postgres in schema public
  grant select, insert, update, delete on tables to service_role;
alter default privileges for role postgres in schema public
  grant usage, select, update on sequences to service_role;

create table if not exists public.bridge_target_quota_rules (
  domain text not null check (domain in ('CPR','STAR','GOV','UNI')),
  cohort_code text not null,
  display_name text not null,
  expected_count integer not null check (expected_count > 0),
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (domain, cohort_code)
);

alter table public.bridge_target_quota_rules enable row level security;
create policy "public read active target quotas" on public.bridge_target_quota_rules
  for select to anon, authenticated using (active = true);

insert into public.bridge_target_quota_rules(domain, cohort_code, display_name, expected_count)
values
  ('CPR','BC70','B2C 기업 70선',70),
  ('CPR','BB30','B2B 기업 30선',30),
  ('STAR','AM40','남자 광고모델 40선',40),
  ('STAR','AW40','여자 광고모델 40선',40),
  ('STAR','AN20','라이징 스타 20선',20),
  ('GOV','GM40','중앙행정기관 40선',40),
  ('GOV','GC60','지방자치단체 60선',60)
on conflict (domain, cohort_code) do update set
  display_name = excluded.display_name,
  expected_count = excluded.expected_count,
  active = true,
  updated_at = now();

-- Normalize legacy beta labels without pretending that their quotas are valid.
update public.bridge_entities set subcategory = 'BC70', updated_at = now()
  where domain = 'CPR' and subcategory = 'B2C';
update public.bridge_entities set subcategory = 'BB30', updated_at = now()
  where domain = 'CPR' and subcategory = 'B2B';
update public.bridge_entities set subcategory = 'AM40', updated_at = now()
  where domain = 'STAR' and subcategory = 'AM';
update public.bridge_entities set subcategory = 'AW40', updated_at = now()
  where domain = 'STAR' and subcategory = 'AW';
update public.bridge_entities set subcategory = 'AN20', updated_at = now()
  where domain = 'STAR' and subcategory = 'AN';

create or replace view public.bridge_target_quota_status
with (security_invoker = true) as
select q.domain,
       q.cohort_code,
       q.display_name,
       q.expected_count,
       count(e.id)::integer as actual_count,
       (count(e.id) = q.expected_count) as exact_match
from public.bridge_target_quota_rules q
left join public.bridge_entities e
  on e.domain = q.domain
 and e.subcategory = q.cohort_code
 and e.active = true
where q.active = true
group by q.domain, q.cohort_code, q.display_name, q.expected_count;

grant select, insert, update, delete on all tables in schema public to service_role;
grant usage, select, update on all sequences in schema public to service_role;
grant select on public.bridge_target_quota_rules,
                public.bridge_target_quota_status to anon, authenticated;

commit;
