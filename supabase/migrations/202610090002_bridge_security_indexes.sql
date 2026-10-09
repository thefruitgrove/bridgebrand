begin;

-- Explicit least-privilege posture for internal evidence and scoring tables.
revoke all on table public.bridge_methodology_versions from anon, authenticated;
revoke all on table public.bridge_source_registry from anon, authenticated;
revoke all on table public.bridge_collection_runs from anon, authenticated;
revoke all on table public.bridge_raw_items from anon, authenticated;
revoke all on table public.bridge_signals from anon, authenticated;
revoke all on table public.bridge_axis_observations from anon, authenticated;
revoke all on table public.bridge_scores from anon, authenticated;
revoke all on table public.bridge_pipeline_alerts from anon, authenticated;

grant select on table public.bridge_entities, public.bridge_rankings to anon, authenticated;
grant select on table public.bridge_public_latest_rankings to anon, authenticated;

create policy "deny direct public methodology access" on public.bridge_methodology_versions
  for all to anon, authenticated using (false) with check (false);
create policy "deny direct public source registry access" on public.bridge_source_registry
  for all to anon, authenticated using (false) with check (false);
create policy "deny direct public collection run access" on public.bridge_collection_runs
  for all to anon, authenticated using (false) with check (false);
create policy "deny direct public raw item access" on public.bridge_raw_items
  for all to anon, authenticated using (false) with check (false);
create policy "deny direct public signal access" on public.bridge_signals
  for all to anon, authenticated using (false) with check (false);
create policy "deny direct public observation access" on public.bridge_axis_observations
  for all to anon, authenticated using (false) with check (false);
create policy "deny direct public score access" on public.bridge_scores
  for all to anon, authenticated using (false) with check (false);
create policy "deny direct public alert access" on public.bridge_pipeline_alerts
  for all to anon, authenticated using (false) with check (false);

-- Foreign-key indexes used by joins, cleanup jobs, and audit drill-downs.
create index if not exists bridge_axis_observations_methodology_idx
  on public.bridge_axis_observations(methodology_version);
create index if not exists bridge_pipeline_alerts_run_idx
  on public.bridge_pipeline_alerts(run_id);
create index if not exists bridge_rankings_entity_idx
  on public.bridge_rankings(entity_id);
create index if not exists bridge_rankings_methodology_idx
  on public.bridge_rankings(methodology_version);
create index if not exists bridge_raw_items_collection_run_idx
  on public.bridge_raw_items(collection_run_id);
create index if not exists bridge_scores_methodology_idx
  on public.bridge_scores(methodology_version);
create index if not exists bridge_signals_raw_item_idx
  on public.bridge_signals(raw_item_id);
create index if not exists bridge_signals_source_idx
  on public.bridge_signals(source_id);

commit;
