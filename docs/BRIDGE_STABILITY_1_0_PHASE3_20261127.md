# BRIDGE Stability 1.0 Phase 3 — Atomic DB publication + live incident escalation
Date: 2026-11-27
Owner: BRIDGE operations / thefruitgrove/bridgebrand

## Incident origin and problem
The legacy `publish_daily_beta` sent two independent PATCH calls to PostgREST:
clear published_at then mark ranks published. A failure between those calls could
leave the same-date database temporarily or permanently without published ranks.
The 2026-11-26/27 rank tie incident had already demonstrated that downstream
export may fail after a DB publication mutation.

## Implemented protection
1. A service-role-only, SECURITY INVOKER Postgres RPC validates the current
   date+methodology, exactly 4 × 100 rankings, unique ordinal ranks, score
   ordering, score/trust linkage and associated current-date metrics.
2. In the same PostgreSQL transaction it locks the staged ranking rows and
   performs **one idempotent UPDATE** setting `published_at` without clearing
   values first. A SQL exception aborts the entire transaction.
3. Python retains its read-only prepublication diagnostic and invokes the
   single RPC instead of two PATCH requests. A malformed response is an error.
4. Existing daily/recovery workflows inherit this change. No metric, rank,
   evidence or scoring rule is altered.
5. The 08:30 KST live verification creates or updates one deduplicated GitHub
   Issue if the public JSON, freshness, or THIS WEEK date check fails. After
   successful verification the incident Issue is closed with a recovery link.
   GitHub notifications depend on account subscription settings; this is not
   an external email/SMS guarantee.
6. Tests cover successful RPC, no-PATCH safety, precheck block, failed RPC,
   malformed response and idempotent replay.

## Transaction boundary — important
This only makes **database publication atomic**. A DB transaction cannot
atomically commit GitHub and Cloudflare. Source JSON generation, git push and
Cloudflare deployment are separate operations. The existing recovery workflow
retains DB published records for reconstruction if downstream steps fail; no
date is fabricated. A clean GitHub commit is not proof of Cloudflare live
deployment.

## Secure rollout
A. Merge only after offline QA passes.
B. Apply migration `202611270001_bridge_atomic_daily_publish.sql` to the
   existing Supabase `bridgebrand-production` database, with secrets unchanged.
   Confirm function is SECURITY INVOKER and EXECUTE is granted to service_role
   but not anon/authenticated.
C. Verify SQL contract in read-only manner and run a same-date idempotent
   invocation *only after* inspecting the complete DB snapshot.
D. Verify all domain snapshots and current Git JSON are consistent.
E. At the next scheduled 05:15 collection, inspect score, publish, JSON and
   live health steps. Keep previous valid release if any gate blocks.
F. No Cloudflare config, UI, private token, or record deletion in this phase.

## Runbook
- Source collection failure: see `bridge_collection_runs`, provider status,
  `bridge_pipeline_alerts`, and Phase 2 resume contract.
- DB promotion failure: verify RPC grants, exactly 400 rankings/metrics,
  ordinal ranks and authoritative score-trust match. Do not fix by overwriting
  scores or disabling the check.
- Git export failure: re-run existing evidence-only recovery with the same
  real observation date. Never merely relabel `asOfDate`.
- Live date mismatch: compare GitHub `site/data/latest.json` with
  `https://bridgebrand.co.kr/data/latest.json`, Cloudflare deployment and
  `this-week.html`; check the deduplicated GitHub health Issue.
- After 7 successive scheduled successful runs measure 30-day release SLO,
  source error rates and detected/closed incident durations.

## Change record
GitHub PR and exact SQL migration provide the change history. All successes
of offline tests must be distinguished from verified production DB execution
and live Cloudflare display.
