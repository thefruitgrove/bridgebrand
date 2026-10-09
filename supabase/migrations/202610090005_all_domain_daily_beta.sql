begin;

insert into public.bridge_target_quota_rules(domain, cohort_code, display_name, expected_count)
values
  ('UNI','U60','4년제 대학 60선',60),
  ('UNI','C40','전문대학 40선',40)
on conflict (domain, cohort_code) do update set
  display_name = excluded.display_name,
  expected_count = excluded.expected_count,
  active = true,
  updated_at = now();

update public.bridge_methodology_versions
set config = jsonb_set(
      jsonb_set(config, '{release_policy,daily_domains}', '["CPR","STAR","GOV","UNI"]'::jsonb, true),
      '{beta_eligibility}',
      '{"CPR":{"minimum_source_families":2,"minimum_confidence_score":55},"STAR":{"minimum_source_families":1,"minimum_confidence_score":0},"GOV":{"minimum_source_families":1,"minimum_confidence_score":0},"UNI":{"minimum_source_families":1,"minimum_confidence_score":0}}'::jsonb,
      true
    )
where version = '2026.10-shadow-1';

commit;
