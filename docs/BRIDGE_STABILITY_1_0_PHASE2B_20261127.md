# BRIDGE Stability 1.0 — Phase 2B: Safe same-date target resume
**Date:** 2026-11-27

## Why
The 400-target required `google_news_rss` scan previously restarted from target 1 after a transient provider error. Phase 2A retained already fetched evidence but blocked publication on incomplete scope. Phase 2B permits a later scheduled retry to query only targets not safely completed in the previous failed run.

## Security and evidence invariants
- Resume is allowed **only** from a previous `bridge_collection_runs` attempt with `status=failed`, `diagnostics.partial_evidence_saved=true` (written *only after* all raw, signal and event upserts returned successfully), matching KST observation day, exact timezone-aware collection window, exact methodology version, **exact complete entity ID set**, and unchanged per-target search-name/alias sequence.
- Only entries explicitly marked `success`, with valid integer `fetched_count` and `matched_count`, may be reused. A successful zero-article observation remains a verified empty search; failed/unattempted entities are ALWAYS queried again.
- Previously successful targets reuse their recorded search outcome and stored signals. This does not fabricate an observation, regenerate raw data, or silently substitute carried historical score.
- On each retry the next run still records all target statuses; the required news source is marked `success` only if **every** target has verified success (fresh or persisted). If a transient provider outage continues, it remains `failed`; current publish/health gates remain closed.
- Invalid, stale, legacy, partially persisted or ambiguously scoped checkpoints are rejected. In such cases the complete scan is performed again.
- Resumption reads past records via the existing Supabase REST connection; no schema change, key change or new provider.
- This resumes only the news target scan. The broader scheduled pipeline still runs its existing independent official baselines and release validation.

## Tests and operating procedure
Offline regression cases cover checkpoint scope, changed aliases, mismatched methodology/date/window, incomplete roster, unsupported partial persistence and actual run continuation without re-fetching a proven success. CI runs these as part of `test_news_resilience.py`.

When the first daily scan fails, inspect `bridge_collection_runs.diagnostics.entity_results` and `failed_entity_ids`. At the existing fallback dispatch, the news collector will automatically detect a valid same-date checkpoint and retry incomplete entities. Never manually edit `published_at`, dates or evidence; inspect `tools.verify_export_file` and live verification afterwards.

**Known remaining risks:** External source may stay unavailable for the full day; core response latency remains provider-dependent; `published_at` DB promotion is not yet one transaction. These require monitoring and Phase 3; no continuous availability guarantee has been established.
