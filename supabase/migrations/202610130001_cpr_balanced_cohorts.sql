begin;

update public.bridge_target_quota_rules
set active = false, updated_at = now()
where domain = 'CPR' and cohort_code in ('BC70', 'BB30');

insert into public.bridge_target_quota_rules(domain, cohort_code, display_name, expected_count, active)
values
  ('CPR','BC50','소비자 직접접점 기업 50선',50,true),
  ('CPR','BB50','기업·산업재 중심 기업 50선',50,true),
  ('UNI','U60','일반·4년제 대학 60선',60,true),
  ('UNI','C40','전문대학 40선',40,true)
on conflict (domain, cohort_code) do update set
  display_name = excluded.display_name,
  expected_count = excluded.expected_count,
  active = excluded.active,
  updated_at = now();

commit;
