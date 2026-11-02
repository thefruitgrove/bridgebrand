-- Restore the public read contract after the October 2026 Data API privilege change.
-- Row visibility remains constrained by the existing publicity_release_clock RLS policy.
grant select on table public.bridge_publicity_articles to anon, authenticated;
