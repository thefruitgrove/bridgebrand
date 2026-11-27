-- BRIDGE Stability 1.0 Phase 3: transactional promotion of an already-scored T100.
-- SECURITY INVOKER: the production service role (never anonymous callers)
-- must own the underlying rights. No score, evidence or ranking is altered.
create or replace function public.bridge_publish_daily_atomic(
  p_date date,
  p_version text
) returns jsonb
language plpgsql
security invoker
set search_path = ''
as $function$
declare
  v_total integer;
  v_group_count integer;
  v_bad integer;
  v_affected integer;
  v_existing integer;
  v_published_at timestamptz := now();
begin
  if p_date is null or p_version is null or length(btrim(p_version)) = 0 then
    raise exception 'BRIDGE_PUBLISH_INVALID_SCOPE' using errcode = '22023';
  end if;
  if p_date > (now() at time zone 'Asia/Seoul')::date then
    raise exception 'BRIDGE_PUBLISH_FUTURE_DATE' using errcode = '22023';
  end if;

  -- Lock the staged current-date ranking rows until the transaction commits.
  -- Coordinated GitHub Actions use one production concurrency group.
  perform 1 from public.bridge_rankings
  where as_of_date=p_date and methodology_version=p_version
    and domain in ('CPR','STAR','GOV','UNI') and ranking_type='T100'
  for update;

  select count(*), count(*) filter (where published_at is not null)
  into v_total,v_existing
  from public.bridge_rankings
  where as_of_date=p_date and methodology_version=p_version
    and domain in ('CPR','STAR','GOV','UNI') and ranking_type='T100';
  if v_total <> 400 then
    raise exception 'BRIDGE_PUBLISH_INCOMPLETE_RANKINGS: %',v_total using errcode='23514';
  end if;

  select count(*) into v_group_count from (
    select domain from public.bridge_rankings
    where as_of_date=p_date and methodology_version=p_version
      and domain in ('CPR','STAR','GOV','UNI') and ranking_type='T100'
    group by domain
    having count(*)=100 and count(distinct rank)=100
      and min(rank)=1 and max(rank)=100
      and count(distinct entity_id)=100
  ) good;
  if v_group_count <> 4 then
    raise exception 'BRIDGE_PUBLISH_BAD_DOMAIN_RANKS' using errcode='23514';
  end if;

  select count(*) into v_bad from (
    select domain,rank,score,
      lag(score) over (partition by domain order by rank) previous_score
    from public.bridge_rankings
    where as_of_date=p_date and methodology_version=p_version
      and domain in ('CPR','STAR','GOV','UNI') and ranking_type='T100'
  ) sorted
  where score is null or score < 0 or score > 100
    or (previous_score is not null and previous_score < score);
  if v_bad <> 0 then
    raise exception 'BRIDGE_PUBLISH_SCORE_ORDER_ERROR: %',v_bad using errcode='23514';
  end if;

  -- Verify authoritative score, grade and metric linkage in the same txn.
  select count(*) into v_bad
  from public.bridge_rankings r
  left join public.bridge_scores s
    on s.entity_id=r.entity_id and s.as_of_date=r.as_of_date
    and s.methodology_version=r.methodology_version
  left join public.bridge_index_metrics m
    on m.entity_id=r.entity_id and m.as_of_date=r.as_of_date
    and m.methodology_version=r.methodology_version
  where r.as_of_date=p_date and r.methodology_version=p_version
    and r.domain in ('CPR','STAR','GOV','UNI') and r.ranking_type='T100'
    and (s.entity_id is null or m.entity_id is null
      or s.score is distinct from r.score
      or s.trust_grade is distinct from r.trust_grade);
  if v_bad <> 0 then
    raise exception 'BRIDGE_PUBLISH_SCORE_TRUST_METRIC_MISMATCH: %',v_bad using errcode='23514';
  end if;

  -- Prevent extra unscored daily metrics outside the fixed four-domain panel.
  select count(*) into v_bad from public.bridge_index_metrics m
  where m.as_of_date=p_date and m.methodology_version=p_version
    and not exists (
      select 1 from public.bridge_rankings r
      where r.entity_id=m.entity_id and r.as_of_date=m.as_of_date
        and r.methodology_version=m.methodology_version
        and r.domain in ('CPR','STAR','GOV','UNI') and r.ranking_type='T100'
    );
  if v_bad <> 0 then
    raise exception 'BRIDGE_PUBLISH_ORPHAN_METRICS: %',v_bad using errcode='23514';
  end if;

  -- Only one UPDATE: no intermediate unpublish state. Any error rolls back.
  update public.bridge_rankings
  set published_at=coalesce(published_at,v_published_at)
  where as_of_date=p_date and methodology_version=p_version
    and domain in ('CPR','STAR','GOV','UNI') and ranking_type='T100';
  get diagnostics v_affected = row_count;
  if v_affected <> 400 then
    raise exception 'BRIDGE_PUBLISH_UPDATE_COUNT: %',v_affected using errcode='23514';
  end if;
  return jsonb_build_object(
    'status',case when v_existing=400 then 'already_published' else 'published' end,
    'asOfDate',p_date,'methodologyVersion',p_version,
    'verifiedRows',400,'affectedRows',v_affected
  );
end;
$function$;

revoke all on function public.bridge_publish_daily_atomic(date,text) from public;
revoke all on function public.bridge_publish_daily_atomic(date,text) from anon,authenticated;
grant execute on function public.bridge_publish_daily_atomic(date,text) to service_role;
