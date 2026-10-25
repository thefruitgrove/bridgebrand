-- The daily scoring window filters and deterministically pages raw evidence by
-- publication time and UUID. The composite index prevents high-volume news
-- days from falling back to a statement-timeout-prone range scan.
create index if not exists bridge_raw_items_published_id_idx
  on public.bridge_raw_items (published_at asc, id asc);
