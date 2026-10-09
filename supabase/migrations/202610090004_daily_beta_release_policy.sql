begin;

update public.bridge_methodology_versions
set config = jsonb_set(
      config,
      '{release_policy}',
      '{"mode":"beta_daily","daily_domains":["CPR","STAR"],"public_domain_labels":{"STAR":"ENT"},"daily_ranking_types":["T100"],"cohort_rankings_require_exact_quota":true}'::jsonb,
      true
    )
where version = '2026.10-shadow-1';

commit;
