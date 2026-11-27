# BRIDGE Stability 1.0 — Phase 2A: RSS collection isolation (2026-11-27)

## Original incident
- 2026-11-27: the first scheduled required Google News RSS collection hit HTTP 503 after 3 retries. The one-target exception escaped from a 400-target loop and aborted the whole run.
- A later dispatch succeeded; the remaining publication failure was independently addressed by ordinal rank fixes and the prepublication contract.
- Single-source 429/503 is an external provider problem, NOT evidence of zero reputation or zero mentions.

## Implemented changes
1. `bridge_pipeline/news_resilience.py` isolates exhausted transient HTTP 429/502/503/504, URL errors and timeouts by target.
2. A successful response with zero matching articles remains `success + fetched_count=0`. A failed request is `failed + fetched_count=null`; a circuit-open target is `not_attempted`, never success.
3. Two **consecutive** exhausted transient errors open the provider circuit for remaining targets. This limits repeated calls while Google News is unavailable. A successful query resets the consecutive count.
4. Already successful targets continue through evidence extraction and idempotent raw/signal/event upsert. The overall mandatory `google_news_rss` collection run is marked **failed** if *any* target failed or was not attempted.
5. Failed runs include target-specific `diagnostics.entity_results` and `failed_entity_ids`, and create a critical pipeline alert. Existing `healthcheck` and recovery publication gates remain closed.
6. The daily pipeline and PR QA run offline tests for transient failure isolation, circuit-open records, nontransient error propagation, true empty success and DB failure status.

## Operational implications
- No silent success, no synthetic positive/neutral evidence, no made-up score, no changed BRIDGE 6-axis methodology.
- Existing partial valid evidence is preserved for auditing; full refresh is still required for publication.
- The fallback workflow can re-dispatch a fresh complete run when no daily/recovery job is active.
- Exceptions not safely classified as transient (e.g. HTTP 403 or code defects) continue to fail the whole collector with explicit error.
- The circuit-breaker threshold is intentionally conservative; adjustment requires observed source error statistics, not assumptions.

## Limitations / next phases
- This phase does **not** guarantee a full daily publication during upstream 429/503 outages; it avoids wasteful requests and preserves evidence while blocking false results.
- Phase 2B: optional same-date, per-target resume of failed/unattempted queries needs versioned checkpoint validation and proof of full target coverage before allowing source success.
- Phase 3: atomic publication promotion and automatic Cloudflare live freshness alerting.
- Daily operation must be evaluated across at least seven scheduled production runs.
- No production database migration or secrets changes in Phase 2A.

## Runbook
If `google_news_rss` fails, inspect `bridge_collection_runs.diagnostics.entity_results` for failed versus not_attempted IDs; inspect `bridge_pipeline_alerts` for the source-level failure and provider HTTP code. Do not edit `published_at` or relabel the public JSON date. After provider service resumes, run the normal dated pipeline with all required collectors and verify 400 published rows, authoritative export and Cloudflare.
